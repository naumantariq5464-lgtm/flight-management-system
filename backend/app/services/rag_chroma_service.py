import os
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timezone
from app.models.policy import PolicyDocument, RagApproval
from app.models.booking import Booking
from app.models.fare import FareRule
from app.repositories.booking_repo import BookingRepository
from app.repositories.audit_repo import AuditRepository
from app.schemas.rag import RagQueryRequest, RagQueryResponse
from app.utils.enums import RagApprovalStatus, AuditSource
from app.config.settings import settings
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from rag.retriever import PolicyRetriever

logger = logging.getLogger("FlightSystem.RAG")

class RagChromaService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.booking_repo = BookingRepository(db)
        self.audit_repo = AuditRepository(db)
        
        # Point to rag/chroma_db vector store
        rag_chroma_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "rag", "chroma_db"))
        self.retriever = PolicyRetriever(persist_dir=rag_chroma_path)

    async def _generate_with_groq(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Calls Groq API with LLaMA-3.3 for lightning-fast inference."""
        if not settings.GROQ_API_KEY or "your_groq_api_key" in settings.GROQ_API_KEY:
            return None

        try:
            from groq import AsyncGroq
            groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
            chat_completion = await groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=settings.GROQ_MODEL,
                temperature=0.2,
                max_tokens=600
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"⚠️ Groq API generation failed: {e}. Falling back to structured response.")
            return None

    async def query_policy_with_chroma(self, request: RagQueryRequest) -> RagQueryResponse:
        """Booking-Aware Policy Query using ChromaDB Vector Store + Groq LLaMA-3.3 LLM."""
        is_booking_aware = False
        booking = None
        fare_rule = None

        # 1. Fetch live booking from Neon DB if PNR / booking_id is provided
        if request.booking_id:
            booking = await self.booking_repo.get_by_id(request.booking_id)
            if not booking:
                booking = await self.booking_repo.get_by_pnr(request.booking_id)
            
            if booking:
                is_booking_aware = True
                rule_stmt = select(FareRule).where(FareRule.fare_type == booking.fare_type)
                rule_res = await self.db.execute(rule_stmt)
                fare_rule = rule_res.scalar_one_or_none()

        # 2. Vector search top-3 relevant policy chunks from ChromaDB
        retrieved_context_texts = []
        try:
            matches = self.retriever.retrieve(query=request.query, top_k=3)
            retrieved_context_texts = [m["text"] for m in matches]
        except Exception:
            # Fallback if collection empty
            docs_res = await self.db.execute(select(PolicyDocument).where(PolicyDocument.is_active == True).limit(3))
            retrieved_context_texts = [d.content for d in docs_res.scalars().all()]

        # 3. Formulate Groq LLM Prompts
        system_prompt = (
            "You are the official AerOps Airline Customer Support AI Assistant. "
            "Provide direct, clear, accurate, and conversational answers to the customer's question. "
            "GUIDELINES:\n"
            "- Answer directly in a warm, professional, helpful tone without robotic letter boilerplate (no 'Subject:', no 'Dear Passenger').\n"
            "- Use clean structured bullet points and bold highlights for key terms (e.g., fees, timeframes, baggage limits).\n"
            "- If passenger booking data is provided, explain exactly what applies to their specific fare (Flexible vs Basic Economy).\n"
            "- If no PNR is given, explain the policy rules clearly for both Basic Economy and Flexible tickets so the user gets a complete, clear answer.\n"
            "- Strictly adhere to the retrieved policy terms."
        )

        booking_context = "No specific booking reference provided."
        if is_booking_aware and booking and fare_rule:
            booking_context = (
                f"- PNR: {booking.pnr}\n"
                f"- Fare Type: {booking.fare_type.value}\n"
                f"- Seat Class: {booking.seat_class.value}\n"
                f"- Is Refundable: {'Yes' if fare_rule.is_refundable else 'No'}\n"
                f"- Cancellation Fee: {fare_rule.cancellation_fee_percent}%\n"
                f"- Baggage Allowance: {fare_rule.baggage_allowance_kg}kg"
            )

        user_prompt = (
            f"Customer Question: '{request.query}'\n\n"
            f"Customer Booking Context: {booking_context}\n\n"
            f"Airline Policy Reference Documents:\n"
            f"{chr(10).join(retrieved_context_texts) if retrieved_context_texts else 'Standard airline policies apply.'}\n\n"
            f"Please answer the customer's question directly, clearly, and helpfully."
        )

        # 4. Generate Response with Groq (or fallback template)
        llm_draft = await self._generate_with_groq(system_prompt, user_prompt)
        
        if not llm_draft:
            if is_booking_aware and booking and fare_rule:
                llm_draft = (
                    f"Regarding your inquiry for booking **PNR: {booking.pnr}** ({booking.fare_type.value} - {booking.seat_class.value} Class):\n\n"
                    f"- **Refundable**: {'Yes' if fare_rule.is_refundable else 'No (Basic Economy)'}\n"
                    f"- **Cancellation Fee**: {fare_rule.cancellation_fee_percent}%\n"
                    f"- **Baggage Allowance**: {fare_rule.baggage_allowance_kg}kg\n\n"
                    f"**Applicable Policy Terms**:\n"
                    f"{retrieved_context_texts[0] if retrieved_context_texts else 'Standard fare rules apply.'}"
                )
            else:
                llm_draft = (
                    f"Here are the applicable airline policy details regarding your question:\n\n"
                    f"{retrieved_context_texts[0] if retrieved_context_texts else 'Standard policy terms apply.'}\n\n"
                    f"💡 *Tip: Provide your 6-character PNR code above to check rules for your specific ticket.*"
                )

        # 5. Save to rag_approvals queue in Neon DB for mandatory supervisor sign-off
        approval = RagApproval(
            customer_query=request.query,
            booking_id=booking.id if booking else None,
            recipient_email=request.recipient_email,
            retrieved_context="\n---\n".join(retrieved_context_texts),
            draft_response=llm_draft,
            status=RagApprovalStatus.PENDING
        )
        self.db.add(approval)
        await self.db.flush()

        # 6. Audit Log
        await self.audit_repo.create_log(
            action="RAG_GROQ_QUERY",
            entity_type="RagApproval",
            entity_id=approval.id,
            actor_email=request.recipient_email,
            new_values={
                "pnr": booking.pnr if booking else None,
                "is_booking_aware": is_booking_aware,
                "model_used": settings.GROQ_MODEL
            },
            source=AuditSource.FASTAPI
        )

        return RagQueryResponse(
            approval_id=approval.id,
            draft_response=llm_draft,
            is_booking_aware=is_booking_aware,
            policy_category_matched="GROQ_LLAMA3_CHROMA",
            status=RagApprovalStatus.PENDING
        )
