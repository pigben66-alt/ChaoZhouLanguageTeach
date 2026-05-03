import uuid
import re
from datetime import datetime, date, timedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.models import (
    User, UserProfile, AbilitySnapshot, LearningRecord, KnowledgeMastery,
    PasswordResetToken, VerificationCode, ActivityLog, UserRole,
)
from app.schemas.user import (
    UserRegister, UserProfileUpdate, SendVerificationCodeRequest, ForgotPasswordRequest,
)
from app.utils.security import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    create_password_reset_token, create_verification_code,
)
from app.utils.helpers import paginate, calc_total_pages

settings = get_settings()


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _validate_phone(self, phone: str) -> bool:
        pattern = r"^1[3-9]\d{9}$"
        return bool(re.match(pattern, phone))

    def _sanitize_input(self, text: str) -> str:
        return re.sub(r"[<>'\";&]", "", text)

    async def send_verification_code(self, phone: str, code_type: str = "register") -> dict:
        if not self._validate_phone(phone):
            raise ValueError("手机号格式不正确")

        await self.db.execute(
            VerificationCode.__table__.delete().where(
                and_(
                    VerificationCode.phone == phone,
                    VerificationCode.code_type == code_type,
                    VerificationCode.used_at.is_(None),
                )
            )
        )

        code = create_verification_code()

        existing = await self.db.execute(
            select(VerificationCode).where(
                and_(
                    VerificationCode.phone == phone,
                    VerificationCode.code_type == code_type,
                )
            )
        )
        existing_code = existing.scalar_one_or_none()

        if existing_code:
            if existing_code.created_at > datetime.utcnow() - timedelta(seconds=60):
                raise ValueError("发送过于频繁，请稍后再试")
            existing_code.code = code
            existing_code.created_at = datetime.utcnow()
            existing_code.expires_at = datetime.utcnow() + timedelta(minutes=10)
        else:
            new_code = VerificationCode(
                phone=phone,
                code=code,
                code_type=code_type,
                expires_at=datetime.utcnow() + timedelta(minutes=10),
            )
            self.db.add(new_code)

        await self.db.flush()

        return {
            "message": "验证码发送成功",
            "code": code if settings.DEBUG else "******",
        }

    async def verify_code(self, phone: str, code: str, code_type: str) -> bool:
        result = await self.db.execute(
            select(VerificationCode).where(
                and_(
                    VerificationCode.phone == phone,
                    VerificationCode.code == code,
                    VerificationCode.code_type == code_type,
                    VerificationCode.used_at.is_(None),
                )
            )
        )
        record = result.scalar_one_or_none()

        if not record or record.expires_at < datetime.utcnow():
            return False

        record.used_at = datetime.utcnow()
        await self.db.flush()
        return True

    async def register(self, data: UserRegister, ip_address: str | None = None) -> User:
        if not self._validate_phone(data.phone):
            raise ValueError("手机号格式不正确")

        if not await self.verify_code(data.phone, data.verification_code, "register"):
            raise ValueError("验证码错误或已过期")

        existing = await self.db.execute(
            select(User).where(User.phone == data.phone)
        )
        if existing.scalar_one_or_none():
            raise ValueError("该手机号已注册")

        user = User(
            phone=data.phone,
            nickname=self._sanitize_input(data.nickname) or f"用户{data.phone[-4:]}",
            password_hash=hash_password(data.password),
            is_verified=True,
        )
        self.db.add(user)
        await self.db.flush()

        profile = UserProfile(user_id=user.id)
        self.db.add(profile)

        await self._log_activity(user.id, "register", "user", str(user.id), None, ip_address)

        await self.db.flush()
        return user

    async def login(self, phone: str, password: str, ip_address: str | None = None) -> dict:
        result = await self.db.execute(select(User).where(User.phone == phone))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash or ""):
            raise ValueError("手机号或密码错误")

        if not user.is_active:
            raise ValueError("账号已被禁用")

        user.last_login_at = datetime.utcnow()
        user.last_login_ip = ip_address
        await self.db.flush()

        await self._log_activity(user.id, "login", "user", str(user.id), None, ip_address)

        user_id_str = str(user.id)
        access_token = create_access_token(user_id_str, user.role)
        refresh_token = create_refresh_token(user_id_str)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "phone": user.phone,
                "nickname": user.nickname,
                "avatar_url": user.avatar_url,
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at,
            },
        }

    async def refresh_token(self, refresh_token_str: str) -> dict:
        from app.utils.security import verify_refresh_token
        payload = verify_refresh_token(refresh_token_str)
        if not payload:
            raise ValueError("无效的刷新令牌")

        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("无效的刷新令牌")

        result = await self.db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise ValueError("用户不存在或已禁用")

        access_token = create_access_token(str(user.id), user.role)
        new_refresh_token = create_refresh_token(str(user.id))

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "phone": user.phone,
                "nickname": user.nickname,
                "avatar_url": user.avatar_url,
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at,
            },
        }

    async def forgot_password(self, data: ForgotPasswordRequest, ip_address: str | None = None) -> dict:
        if not await self.verify_code(data.phone, data.verification_code, "forgot_password"):
            raise ValueError("验证码错误或已过期")

        result = await self.db.execute(select(User).where(User.phone == data.phone))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("用户不存在")

        reset_token = create_password_reset_token()

        password_reset = PasswordResetToken(
            user_id=user.id,
            token=reset_token,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        self.db.add(password_reset)
        await self.db.flush()

        await self._log_activity(user.id, "password_reset_request", "user", str(user.id), None, ip_address)

        return {
            "message": "密码重置链接已生成",
            "reset_token": reset_token if settings.DEBUG else "******",
        }

    async def reset_password(self, token: str, new_password: str, ip_address: str | None = None) -> bool:
        result = await self.db.execute(
            select(PasswordResetToken).where(
                and_(
                    PasswordResetToken.token == token,
                    PasswordResetToken.used_at.is_(None),
                )
            )
        )
        reset_record = result.scalar_one_or_none()

        if not reset_record or reset_record.expires_at < datetime.utcnow():
            raise ValueError("重置链接已过期")

        user_id = reset_record.user_id
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        if not user:
            raise ValueError("用户不存在")

        user.password_hash = hash_password(new_password)
        reset_record.used_at = datetime.utcnow()

        await self._log_activity(user.id, "password_reset_complete", "user", str(user.id), None, ip_address)

        await self.db.flush()
        return True

    async def change_password(self, user_id: uuid.UUID, old_password: str, new_password: str, ip_address: str | None = None) -> bool:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not verify_password(old_password, user.password_hash or ""):
            raise ValueError("原密码错误")

        user.password_hash = hash_password(new_password)

        await self._log_activity(user.id, "password_change", "user", str(user.id), None, ip_address)

        await self.db.flush()
        return True

    async def get_profile(self, user_id: uuid.UUID) -> UserProfile | None:
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_profile(self, user_id: uuid.UUID, data: UserProfileUpdate) -> UserProfile:
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise ValueError("用户档案不存在")

        if data.native_language is not None:
            profile.native_language = self._sanitize_input(data.native_language)
        if data.self_eval_level is not None:
            profile.self_eval_level = data.self_eval_level

        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            if data.nickname is not None:
                user.nickname = self._sanitize_input(data.nickname)
            if data.avatar_url is not None:
                user.avatar_url = self._sanitize_input(data.avatar_url)

        await self.db.flush()
        return profile

    async def get_progress(self, user_id: uuid.UUID) -> dict:
        profile = await self.get_profile(user_id)
        if not profile:
            raise ValueError("用户档案不存在")

        lessons_count = await self.db.execute(
            select(func.count(LearningRecord.id)).where(
                and_(
                    LearningRecord.user_id == user_id,
                    LearningRecord.record_type == "lesson_complete",
                )
            )
        )
        total_lessons = lessons_count.scalar() or 0

        practice_count = await self.db.execute(
            select(func.count(LearningRecord.id)).where(LearningRecord.user_id == user_id)
        )
        total_practice = practice_count.scalar() or 0

        dialogue_count = await self.db.execute(
            select(func.count(LearningRecord.id)).where(
                and_(
                    LearningRecord.user_id == user_id,
                    LearningRecord.record_type == "dialogue_complete",
                )
            )
        )
        total_dialogue = dialogue_count.scalar() or 0

        return {
            "current_level": profile.current_level,
            "total_study_sec": profile.total_study_sec,
            "streak_days": profile.streak_days,
            "vocab_mastered": profile.vocab_mastered,
            "tone_accuracy": profile.tone_accuracy,
            "grammar_accuracy": profile.grammar_accuracy,
            "listening_accuracy": profile.listening_accuracy,
            "speaking_accuracy": profile.speaking_accuracy,
            "total_lessons_completed": total_lessons,
            "total_practice_count": total_practice,
            "total_dialogue_count": total_dialogue,
        }

    async def get_latest_ability(self, user_id: uuid.UUID) -> AbilitySnapshot | None:
        result = await self.db.execute(
            select(AbilitySnapshot)
            .where(AbilitySnapshot.user_id == user_id)
            .order_by(AbilitySnapshot.evaluated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update_streak(self, user_id: uuid.UUID):
        profile = await self.get_profile(user_id)
        if not profile:
            return

        today = date.today()
        if profile.last_study_date == today:
            return

        if profile.last_study_date and (today - profile.last_study_date).days == 1:
            profile.streak_days += 1
        elif profile.last_study_date and (today - profile.last_study_date).days > 1:
            profile.streak_days = 1
        else:
            profile.streak_days = max(1, profile.streak_days)

        profile.last_study_date = today
        await self.db.flush()

    async def get_user_activity_logs(
        self, user_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> tuple[list[ActivityLog], int]:
        offset, limit = paginate(page, page_size)

        query = (
            select(ActivityLog)
            .where(ActivityLog.user_id == user_id)
            .order_by(ActivityLog.created_at.desc())
        )

        total_result = await self.db.execute(
            select(func.count(ActivityLog.id)).where(ActivityLog.user_id == user_id)
        )
        total = total_result.scalar() or 0

        result = await self.db.execute(query.offset(offset).limit(limit))
        items = list(result.scalars().all())

        return items, total

    async def _log_activity(
        self, user_id: uuid.UUID, action: str, resource_type: str | None,
        resource_id: str | None, detail: dict | None, ip_address: str | None
    ):
        log = ActivityLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail,
            ip_address=ip_address,
        )
        self.db.add(log)
        await self.db.flush()
