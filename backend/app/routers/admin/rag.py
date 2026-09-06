from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database.session import get_db
from app.schemas.rag import RagApprovalOut, RagApprovalAction, PolicyDocumentCreate, PolicyDocumentOut
from app.models.policy import PolicyDocument
from app.models.user import User
from app.services.rag_service import RagService
from app.auth.dependencies import get_admin_user

router = APIRouter(prefix="/admin/rag", tags=["Admin RAG & Policy Approvals"])

@router.get("/approvals", response_model=List[RagApprovalOut])
async def list_rag_approvals(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    service = RagService(db)
    items = await service.list_pending_approvals(skip, limit)
    return [RagApprovalOut.model_validate(i) for i in items]

@router.post("/approvals/{approval_id}/action", response_model=RagApprovalOut)
async def take_rag_approval_action(
    approval_id: str,
    action: RagApprovalAction,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    service = RagService(db)
    updated = await service.review_approval(approval_id, action, admin_user=current_user)
    return RagApprovalOut.model_validate(updated)

@router.post("/documents", response_model=PolicyDocumentOut, status_code=status.HTTP_201_CREATED)
async def create_policy_document(
    data: PolicyDocumentCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    doc = PolicyDocument(
        title=data.title,
        category=data.category.upper(),
        content=data.content,
        file_name=data.file_name,
        is_active=True,
        version=1
    )
    db.add(doc)
    await db.flush()
    return PolicyDocumentOut.model_validate(doc)

@router.get("/documents", response_model=List[PolicyDocumentOut])
async def list_policy_documents(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(PolicyDocument).where(PolicyDocument.is_active == True))
    return [PolicyDocumentOut.model_validate(d) for d in res.scalars().all()]
