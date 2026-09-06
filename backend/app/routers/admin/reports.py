from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.reports import DashboardStats, ReportResponse
from app.models.user import User
from app.services.report_service import ReportService
from app.auth.dependencies import get_admin_user

router = APIRouter(prefix="/admin/reports", tags=["Admin Reports & Analytics"])

@router.get("/dashboard", response_model=DashboardStats)
@router.get("/daily-summary", response_model=DashboardStats)
async def get_dashboard_summary(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    service = ReportService(db)
    return await service.get_dashboard_stats()

@router.get("/full", response_model=ReportResponse)
async def get_full_operational_report(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    service = ReportService(db)
    return await service.get_full_report()
