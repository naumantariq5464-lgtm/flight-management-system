from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import List, Optional
from datetime import datetime, timezone
from app.models.policy import PolicyDocument, RagApproval
from app.models.booking import Booking
from app.models.fare import FareRule
from app.models.user import User
from app.repositories.booking_repo import BookingRepository
from app.repositories.audit_repo import AuditRepository
from app.schemas.rag import RagQueryRequest, RagQueryResponse, RagApprovalAction
from app.utils.enums import RagApprovalStatus, AuditSource
from app.utils.exceptions import NotFoundException, BadRequestException

class RagService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.booking_repo = BookingRepository(db)
        self.audit_repo = AuditRepository(db)

    async def query_policy(self, request: RagQueryRequest) -> RagQueryResponse:
        """Booking-Aware Policy Assistant: Combines real booking fare rules with knowledge base context."""
        retrieved_context = []
        is_booking_aware = False
        booking = None
        fare_rule = None

        # 1. Fetch Booking and Fare Rule if booking_id provided
        if request.booking_id:
            booking = await self.booking_repo.get_by_id(request.booking_id)
            if not booking:
                # Try finding by PNR
                booking = await self.booking_repo.get_by_pnr(request.booking_id)
            
            if booking:
                is_booking_aware = True
                rule_stmt = select(FareRule).where(FareRule.fare_type == booking.fare_type)
                rule_res = await self.db.execute(rule_stmt)
                fare_rule = rule_res.scalar_one_or_none()

        # 2. Retrieve relevant policy documents from PostgreSQL / Pinecone
        docs_res = await self.db.execute(
            select(PolicyDocument).where(PolicyDocument.is_active == True).limit(5)
        )
        docs = list(docs_res.scalars().all())
        for d in docs:
            retrieved_context.append(f"[{d.category}] {d.title}: {d.content}")

        # 3. Formulate Booking-Aware Draft Response
        if is_booking_aware and booking and fare_rule:
            refund_info = (
                f"Your booking (PNR: {booking.pnr}) is on {booking.fare_type.value} fare in {booking.seat_class.value} class. "
                f"Refundable: {'Yes' if fare_rule.is_refundable else 'No'}. "
                f"Cancellation fee: {fare_rule.cancellation_fee_percent}%. "
                f"Baggage allowance: {fare_rule.baggage_allowance_kg}kg."
            )
            draft = (
                f"Dear Passenger,\n\n"
                f"Regarding your query: '{request.query}'\n\n"
                f"{refund_info}\n\n"
                f"According to airline policy: {fare_rule.description or 'Standard terms apply.'}\n\n"
                f"Best regards,\nFlight Operations Customer Support"
            )
        else:
            draft = (
                f"Dear Passenger,\n\n"
                f"Regarding your query: '{request.query}'\n\n"
                f"Our general airline policy allows changes and refunds based on the specific fare type purchased. "
                f"Flexible fares permit refunds with minimal cancellation fees, while Basic Economy tickets are non-refundable. "
                f"For personalized guidance, please provide your 6-digit PNR booking reference.\n\n"
                f"Best regards,\nFlight Operations Customer Support"
            )

        # 4. Save to RagApproval queue for Human-in-the-Loop review
        approval = RagApproval(
            customer_query=request.query,
            booking_id=booking.id if booking else None,
            recipient_email=request.recipient_email,
            retrieved_context="\n---\n".join(retrieved_context),
            draft_response=draft,
            status=RagApprovalStatus.PENDING
        )
        self.db.add(approval)
        await self.db.flush()

        # 5. Audit Log
        await self.audit_repo.create_log(
            action="RAG_QUERY_GENERATED",
            entity_type="RagApproval",
            entity_id=approval.id,
            actor_email=request.recipient_email,
            new_values={
                "is_booking_aware": is_booking_aware,
                "pnr": booking.pnr if booking else None
            },
            source=AuditSource.FASTAPI
        )

        return RagQueryResponse(
            approval_id=approval.id,
            draft_response=draft,
            is_booking_aware=is_booking_aware,
            policy_category_matched=docs[0].category if docs else "GENERAL",
            status=RagApprovalStatus.PENDING
        )

    async def list_pending_approvals(self, skip: int = 0, limit: int = 50) -> List[RagApproval]:
        stmt = select(RagApproval).order_by(desc(RagApproval.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def review_approval(
        self, 
        approval_id: str, 
        action: RagApprovalAction, 
        admin_user: User
    ) -> RagApproval:
        stmt = select(RagApproval).where(RagApproval.id == approval_id).with_for_update()
        res = await self.db.execute(stmt)
        approval = res.scalar_one_or_none()
        if not approval:
            raise NotFoundException(f"Approval task {approval_id} not found")

        approval.status = action.status
        approval.reviewed_by_user_id = admin_user.id
        approval.reviewed_at = datetime.now(timezone.utc)
        approval.review_notes = action.review_notes
        
        if action.status == RagApprovalStatus.EDITED and action.final_approved_response:
            approval.final_approved_response = action.final_approved_response
        elif action.status == RagApprovalStatus.APPROVED:
            approval.final_approved_response = approval.draft_response

        await self.audit_repo.create_log(
            action=f"RAG_{action.status.value}",
            entity_type="RagApproval",
            entity_id=approval.id,
            actor_email=admin_user.email,
            actor_role=admin_user.role.name.value,
            new_values={"status": action.status.value, "notes": action.review_notes},
            source=AuditSource.ADMIN
        )

        return approval
