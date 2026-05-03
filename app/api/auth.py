import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user_id, get_client_ip
from app.services.user_service import UserService
from app.schemas.user import (
    UserRegister, UserLogin, TokenResponse, RefreshTokenRequest,
    UserProfileResponse, UserProfileUpdate, UserProgressResponse,
    AbilitySnapshotResponse, SendVerificationCodeRequest, VerifyCodeRequest,
    ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest,
)

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


@router.post("/send-code")
async def send_verification_code(data: SendVerificationCodeRequest, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    try:
        return await service.send_verification_code(data.phone, data.code_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/verify-code")
async def verify_code(data: VerifyCodeRequest, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    try:
        valid = await service.verify_code(data.phone, data.code, data.code_type)
        if not valid:
            raise ValueError("验证码错误或已过期")
        return {"message": "验证成功"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister, request: Request, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    try:
        await service.register(data, get_client_ip(request))
        tokens = await service.login(data.phone, data.password, get_client_ip(request))
        return tokens
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    try:
        return await service.login(data.phone, data.password, get_client_ip(request))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, request: Request, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    try:
        return await service.forgot_password(data, get_client_ip(request))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, request: Request, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    try:
        await service.reset_password(data.token, data.new_password, get_client_ip(request))
        return {"message": "密码重置成功"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    try:
        return await service.refresh_token(data.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


user_router = APIRouter(prefix="/api/v1/users", tags=["用户"])


@user_router.get("/me", response_model=dict)
async def get_my_info(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.models import User
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return {
        "id": str(user.id),
        "phone": user.phone,
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "role": user.role,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
    }


@user_router.get("/me/profile", response_model=UserProfileResponse)
async def get_my_profile(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    profile = await service.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户档案不存在")
    return profile


@user_router.put("/me/profile", response_model=UserProfileResponse)
async def update_my_profile(
    data: UserProfileUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    try:
        return await service.update_profile(user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@user_router.post("/me/change-password")
async def change_my_password(
    data: ChangePasswordRequest,
    request: Request,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    try:
        await service.change_password(user_id, data.old_password, data.new_password, get_client_ip(request))
        return {"message": "密码修改成功"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@user_router.get("/me/progress", response_model=UserProgressResponse)
async def get_my_progress(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    try:
        return await service.get_progress(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@user_router.get("/me/ability", response_model=AbilitySnapshotResponse | None)
async def get_my_ability(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.get_latest_ability(user_id)
