from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.rag import RagQueryRequest, RagQueryResponse
from app.services.rag_chroma_service import RagChromaService

router = APIRouter(prefix="/rag", tags=["Customer Policy Assistant"])

@router.post("/query", response_model=RagQueryResponse)
async def query_policy_assistant(
    request: RagQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    service = RagChromaService(db)
    return await service.query_policy_with_chroma(request)
