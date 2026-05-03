import uuid
import re
from datetime import datetime, timedelta, date
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    User, UserProfile, LearningRecord, KnowledgePoint, Vocabulary,
    Lesson, DialogueScene, ContentVersion, ActivityLog, SystemSetting,
    KnowledgeMastery, UserRole, ContentStatus,
)
from app.utils.helpers import paginate, calc_total_pages


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _sanitize_input(self, text: str) -> str:
        return re.sub(r"[<>'\";&]", "", text)

    async def get_dashboard(self) -> dict:
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        total_users = await self.db.execute(select(func.count(User.id)))
        total_users_count = total_users.scalar() or 0

        active_today = await self.db.execute(
            select(func.count(func.distinct(LearningRecord.user_id))).where(
                LearningRecord.created_at >= today_start
            )
        )
        active_today_count = active_today.scalar() or 0

        active_week = await self.db.execute(
            select(func.count(func.distinct(LearningRecord.user_id))).where(
                LearningRecord.created_at >= week_start
            )
        )
        active_week_count = active_week.scalar() or 0

        total_records = await self.db.execute(select(func.count(LearningRecord.id)))
        total_records_count = total_records.scalar() or 0

        today_records = await self.db.execute(
            select(func.count(LearningRecord.id)).where(
                LearningRecord.created_at >= today_start
            )
        )
        today_records_count = today_records.scalar() or 0

        avg_score = await self.db.execute(
            select(func.avg(LearningRecord.score)).where(LearningRecord.score.isnot(None))
        )
        avg_score_val = avg_score.scalar() or 0

        kp_count = await self.db.execute(select(func.count(KnowledgePoint.id)))
        kp_total = kp_count.scalar() or 0

        kp_published = await self.db.execute(
            select(func.count(KnowledgePoint.id)).where(
                KnowledgePoint.status == ContentStatus.PUBLISHED.value
            )
        )
        kp_published_count = kp_published.scalar() or 0

        vocab_count = await self.db.execute(select(func.count(Vocabulary.id)))
        vocab_total = vocab_count.scalar() or 0

        lesson_count = await self.db.execute(select(func.count(Lesson.id)))
        lesson_total = lesson_count.scalar() or 0

        lesson_published = await self.db.execute(
            select(func.count(Lesson.id)).where(Lesson.status == ContentStatus.PUBLISHED.value)
        )
        lesson_published_count = lesson_published.scalar() or 0

        scene_count = await self.db.execute(select(func.count(DialogueScene.id)))
        scene_total = scene_count.scalar() or 0

        scene_published = await self.db.execute(
            select(func.count(DialogueScene.id)).where(
                DialogueScene.status == ContentStatus.PUBLISHED.value
            )
        )
        scene_published_count = scene_published.scalar() or 0

        recent_activities = await self.db.execute(
            select(ActivityLog, User.nickname)
            .join(User, ActivityLog.user_id == User.id, isouter=True)
            .order_by(ActivityLog.created_at.desc())
            .limit(10)
        )

        top_learners = await self.db.execute(
            select(User, UserProfile)
            .join(UserProfile, User.id == UserProfile.user_id, isouter=True)
            .order_by(UserProfile.total_study_sec.desc())
            .limit(5)
        )

        learning_trends = await self._get_learning_trends()

        return {
            "system_stats": {
                "total_users": total_users_count,
                "active_users_today": active_today_count,
                "active_users_week": active_week_count,
                "total_study_records": total_records_count,
                "today_study_records": today_records_count,
                "avg_study_score": round(float(avg_score_val), 1),
                "total_content_items": kp_total + vocab_total + lesson_total + scene_total,
                "published_content_items": kp_published_count + lesson_published_count + scene_published_count,
                "system_uptime": "99.9%",
            },
            "content_stats": {
                "kp_count": kp_total,
                "kp_published": kp_published_count,
                "vocab_count": vocab_total,
                "lesson_count": lesson_total,
                "lesson_published": lesson_published_count,
                "scene_count": scene_total,
                "scene_published": scene_published_count,
            },
            "learning_trends": learning_trends,
            "recent_activities": [
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
                for log, nickname in recent_activities
            ],
            "top_learners": [
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
                    "profile": {
                        "current_level": profile.current_level if profile else 1,
                        "total_study_sec": profile.total_study_sec if profile else 0,
                        "streak_days": profile.streak_days if profile else 0,
                        "vocab_mastered": profile.vocab_mastered if profile else 0,
                        "total_lessons_completed": profile.total_lessons_completed if profile else 0,
                        "total_practice_count": profile.total_practice_count if profile else 0,
                    } if profile else None,
                }
                for user, profile in top_learners
            ],
        }

    async def _get_learning_trends(self, days: int = 7) -> list:
        trends = []
        today = date.today()

        for i in range(days - 1, -1, -1):
            target_date = today - timedelta(days=i)
            target_start = datetime(target_date.year, target_date.month, target_date.day)
            target_end = target_start + timedelta(days=1)

            new_users = await self.db.execute(
                select(func.count(User.id)).where(
                    and_(
                        User.created_at >= target_start,
                        User.created_at < target_end,
                    )
                )
            )

            active_users = await self.db.execute(
                select(func.count(func.distinct(LearningRecord.user_id))).where(
                    and_(
                        LearningRecord.created_at >= target_start,
                        LearningRecord.created_at < target_end,
                    )
                )
            )

            study_records = await self.db.execute(
                select(func.count(LearningRecord.id)).where(
                    and_(
                        LearningRecord.created_at >= target_start,
                        LearningRecord.created_at < target_end,
                    )
                )
            )

            avg_score = await self.db.execute(
                select(func.avg(LearningRecord.score)).where(
                    and_(
                        LearningRecord.created_at >= target_start,
                        LearningRecord.created_at < target_end,
                        LearningRecord.score.isnot(None),
                    )
                )
            )

            trends.append({
                "date": str(target_date),
                "new_users": new_users.scalar() or 0,
                "active_users": active_users.scalar() or 0,
                "study_records": study_records.scalar() or 0,
                "avg_score": round(float(avg_score.scalar() or 0), 1),
            })

        return trends

    async def list_users(
        self, page: int = 1, page_size: int = 20,
        role: str | None = None, is_active: bool | None = None,
        search: str | None = None
    ) -> tuple[list[User], int]:
        offset, limit = paginate(page, page_size)
        conditions = []

        if role:
            conditions.append(User.role == role)
        if is_active is not None:
            conditions.append(User.is_active == is_active)
        if search:
            search_pattern = f"%{self._sanitize_input(search)}%"
            conditions.append(
                or_(
                    User.phone.ilike(search_pattern),
                    User.nickname.ilike(search_pattern),
                )
            )

        query = select(User).order_by(User.created_at.desc())
        count_query = select(func.count(User.id))

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        result = await self.db.execute(query.offset(offset).limit(limit))
        items = list(result.scalars().all())

        return items, total

    async def get_user_detail(self, user_id: uuid.UUID) -> dict | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return None

        profile_result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()

        records_result = await self.db.execute(
            select(LearningRecord).where(LearningRecord.user_id == user_id).order_by(LearningRecord.created_at.desc()).limit(100)
        records = list(records_result.scalars().all())

        total_records = await self.db.execute(
            select(func.count(LearningRecord.id)).where(LearningRecord.user_id == user_id)
        )
        total_records_count = total_records.scalar() or 0

        avg_score_result = await self.db.execute(
            select(func.avg(LearningRecord.score)).where(
                and_(LearningRecord.user_id == user_id, LearningRecord.score.isnot(None))
            )
        )
        avg_score = avg_score_result.scalar() or 0

        unique_days_result = await self.db.execute(
            select(func.count(func.distinct(func.date(LearningRecord.created_at)))).where(
                LearningRecord.user_id == user_id
            )
        )
        active_days = unique_days_result.scalar() or 0

        record_types_result = await self.db.execute(
            select(LearningRecord.record_type, func.count(LearningRecord.id))
            .where(LearningRecord.user_id == user_id)
            .group_by(LearningRecord.record_type)
            .order_by(func.count(LearningRecord.id).desc())
            .limit(1)
        )
        dominant_type = record_types_result.first()

        return {
            "id": user.id,
            "phone": user.phone,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "role": user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at,
            "profile": profile,
            "stats": {
                "total_study_hours": round((profile.total_study_sec if profile else 0) / 3600, 1),
                "avg_daily_study_minutes": round(
                    ((profile.total_study_sec if profile else 0) / max(1, active_days)) / 60, 1
                ) if active_days > 0 else 0,
                "avg_score": round(float(avg_score), 1),
                "total_sessions": total_records_count,
                "active_days": active_days,
                "dominant_learn_type": dominant_type[0] if dominant_type else None,
            },
        }

    async def update_user_role(self, user_id: uuid.UUID, role: str) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return None

        if role not in [UserRole.USER.value, UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
            raise ValueError("无效的角色")

        user.role = role
        await self.db.flush()
        return user

    async def toggle_user_status(self, user_id: uuid.UUID, is_active: bool) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return None

        user.is_active = is_active
        await self.db.flush()
        return user

    async def publish_content(self, content_type: str, content_id: uuid.UUID, action: str) -> dict:
        if action == "publish":
            if content_type == "kp":
                result = await self.db.execute(
                    select(KnowledgePoint).where(KnowledgePoint.id == content_id)
                )
                item = result.scalar_one_or_none()
                if item:
                    item.status = ContentStatus.PUBLISHED.value
            elif content_type == "lesson":
                result = await self.db.execute(select(Lesson).where(Lesson.id == content_id))
                item = result.scalar_one_or_none()
                if item:
                    item.status = ContentStatus.PUBLISHED.value
            elif content_type == "scene":
                result = await self.db.execute(
                    select(DialogueScene).where(DialogueScene.id == content_id)
                )
                item = result.scalar_one_or_none()
                if item:
                    item.status = ContentStatus.PUBLISHED.value

            await self.db.flush()
            return {"status": "published", "content_type": content_type, "content_id": str(content_id)}

        elif action == "archive":
            if content_type == "kp":
                result = await self.db.execute(
                    select(KnowledgePoint).where(KnowledgePoint.id == content_id)
                )
                item = result.scalar_one_or_none()
                if item:
                    item.status = ContentStatus.ARCHIVED.value
            elif content_type == "lesson":
                result = await self.db.execute(select(Lesson).where(Lesson.id == content_id))
                item = result.scalar_one_or_none()
                if item:
                    item.status = ContentStatus.ARCHIVED.value
            elif content_type == "scene":
                result = await self.db.execute(
                    select(DialogueScene).where(DialogueScene.id == content_id)
                )
                item = result.scalar_one_or_none()
                if item:
                    item.status = ContentStatus.ARCHIVED.value

            await self.db.flush()
            return {"status": "archived", "content_type": content_type, "content_id": str(content_id)}

        raise ValueError("无效的操作")

    async def get_content_versions(
        self, content_type: str, content_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> tuple[list[ContentVersion], int]:
        offset, limit = paginate(page, page_size)

        if content_type == "kp":
            query = select(ContentVersion).where(ContentVersion.kp_id == content_id)
            count_query = select(func.count(ContentVersion.id)).where(ContentVersion.kp_id == content_id)
        elif content_type == "lesson":
            query = select(ContentVersion).where(ContentVersion.lesson_id == content_id)
            count_query = select(func.count(ContentVersion.id)).where(ContentVersion.lesson_id == content_id)
        elif content_type == "scene":
            query = select(ContentVersion).where(ContentVersion.dialogue_scene_id == content_id)
            count_query = select(func.count(ContentVersion.id)).where(
                ContentVersion.dialogue_scene_id == content_id
            )
        else:
            return [], 0

        query = query.order_by(ContentVersion.created_at.desc())

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        result = await self.db.execute(query.offset(offset).limit(limit))
        items = list(result.scalars().all())

        return items, total

    async def list_activity_logs(
        self, page: int = 1, page_size: int = 20,
        user_id: uuid.UUID | None = None, action: str | None = None
    ) -> tuple[list[ActivityLog], int]:
        offset, limit = paginate(page, page_size)
        conditions = []

        if user_id:
            conditions.append(ActivityLog.user_id == user_id)
        if action:
            conditions.append(ActivityLog.action == action)

        query = (
            select(ActivityLog, User.nickname)
            .join(User, ActivityLog.user_id == User.id, isouter=True)
            .order_by(ActivityLog.created_at.desc())
        )
        count_query = select(func.count(ActivityLog.id))

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        result = await self.db.execute(query.offset(offset).limit(limit))
        items = [(log, nickname) for log, nickname in result]

        return items, total

    async def get_system_settings(self) -> list[SystemSetting]:
        result = await self.db.execute(select(SystemSetting).order_by(SystemSetting.key))
        return list(result.scalars().all())

    async def update_system_setting(
        self, key: str, value: dict, admin_id: uuid.UUID
    ) -> SystemSetting:
        result = await self.db.execute(select(SystemSetting).where(SystemSetting.key == key))
        setting = result.scalar_one_or_none()

        if setting:
            setting.value = value
            setting.updated_by = admin_id
            setting.updated_at = datetime.utcnow()
        else:
            setting = SystemSetting(key=key, value=value, updated_by=admin_id)
            self.db.add(setting)

        await self.db.flush()
        return setting
