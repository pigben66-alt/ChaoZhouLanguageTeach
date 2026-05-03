import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user_id, require_admin
from app.services.admin_service import AdminService
from app.schemas.admin import (
    AdminUserResponse, AdminUserDetail, AdminUserProfileResponse, AdminUserStatsResponse,
    AdminUpdateUserRole, AdminToggleUserStatus,
    AdminContentPublishRequest, AdminContentVersionResponse,
    AdminActivityLogResponse, AdminSystemStatsResponse,
    AdminLearningTrendResponse, AdminContentStatsResponse, AdminDashboardResponse,
)
from app.utils.helpers import calc_total_pages

router = APIRouter(prefix="/api/v1/admin", tags=["管理员后台"])


@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    request: Request,
    user_id: uuid.UUID = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return await service.get_dashboard()


@router.get("/users")
async def list_admin_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    role: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    user_id: uuid.UUID = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    items, total = await service.list_users(page, page_size, role, is_active, search)

    return {
        "items": [
            {
                "id": str(user.id),
                "phone": user.phone,
                "nickname": user.nickname,
                "avatar_url": user.avatar_url,
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at,
                "last_login_at": user.last_login_at,
            }
            for user in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": calc_total_pages(total, page_size),
    }


@router.get("/users/{target_user_id}")
async def get_admin_user_detail(
    target_user_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    detail = await service.get_user_detail(target_user_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    return detail


@router.post("/users/role")
async def update_user_role(
    data: AdminUpdateUserRole,
    user_id: uuid.UUID = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    try:
        result = await service.update_user_role(data.user_id, data.role)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        return {"message": "角色更新成功"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/users/toggle-status")
async def toggle_user_status(
    data: AdminToggleUserStatus,
    user_id: uuid.UUID = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    result = await service.toggle_user_status(data.user_id, data.is_active)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return {"message": "状态更新成功"}


@router.post("/content/publish")
async def publish_content(
    data: AdminContentPublishRequest,
    user_id: uuid.UUID = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    try:
        return await service.publish_content(data.content_type, data.content_id, data.action)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/content/versions/{content_type}/{content_id}")
async def get_content_versions(
    content_type: str,
    content_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user_id: uuid.UUID = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    items, total = await service.get_content_versions(content_type, content_id, page, page_size)

    return {
        "items": [
            AdminContentVersionResponse.model_validate(item) for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": calc_total_pages(total, page_size),
    }


@router.get("/activity-logs")
async def list_activity_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user_id_filter: uuid.UUID | None = Query(default=None, alias="user_id"),
    action: str | None = Query(default=None),
    user_id: uuid.UUID = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    items, total = await service.list_activity_logs(page, page_size, user_id_filter, action)

    return {
        "items": [
            {
                "id": str(log.id),
                "user_id": str(log.user_id) if log.user_id else None,
                "user_nickname": nickname,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "ip_address": log.ip_address,
                "created_at": log.created_at,
            }
            for log, nickname in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": calc_total_pages(total, page_size),
    }


@router.get("/settings")
async def get_system_settings(
    user_id: uuid.UUID = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    settings = await service.get_system_settings()
    return {"items": [{"key": s.key, "value": s.value, "description": s.description} for s in settings]}
