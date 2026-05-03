import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    DashboardSummary, HeatmapData, RadarData, TrendData, WeaknessItem, ReportResponse,
)

router = APIRouter(prefix="/api/v1/analytics", tags=["数据分析"])


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_dashboard_summary(user_id)


@router.get("/heatmap")
async def get_heatmap(
    month: str | None = Query(default=None, description="格式: YYYY-MM"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    data = await service.get_heatmap(user_id, month)
    return {"items": data, "total": len(data)}


@router.get("/radar", response_model=RadarData)
async def get_radar(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_radar(user_id)


@router.get("/trend", response_model=TrendData)
async def get_trend(
    metric: str = Query(default="score", description="score/duration/count/all"),
    period: str = Query(default="weekly", description="weekly/monthly"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_trend(user_id, metric, period)


@router.get("/weakness")
async def get_weakness(
    top_n: int = Query(default=10, ge=1, le=50),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    items = await service.get_weakness(user_id, top_n)
    return {"items": items, "total": len(items)}


@router.get("/report", response_model=ReportResponse)
async def get_report(
    period: str = Query(default="weekly", description="weekly/monthly"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return ReportResponse(
        report_url=f"/reports/{user_id}/{period}_report.pdf",
        generated_at="2026-05-03T10:00:00Z",
        period=period,
    )
