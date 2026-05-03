import uuid
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    KnowledgePoint, KnowledgeRelation, Vocabulary, Lesson,
    DialogueScene, LearningRecord, KnowledgeMastery,
)
from app.schemas.learning import (
    KnowledgePointCreate, KnowledgePointUpdate, KnowledgeRelationCreate,
    VocabularyCreate, LessonCreate, DialogueSceneCreate, LearningRecordCreate,
    ReviewQueueItem,
)
from app.utils.helpers import paginate, calc_total_pages, bkt_update, sm2_update, days_between


class LearningService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_knowledge_points(
        self, kp_type: str | None = None, level: int | None = None,
        search: str | None = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[KnowledgePoint], int]:
        offset, limit = paginate(page, page_size)
        conditions = []

        if kp_type:
            conditions.append(KnowledgePoint.kp_type == kp_type)
        if level:
            conditions.append(KnowledgePoint.level == level)
        if search:
            conditions.append(
                or_(
                    KnowledgePoint.title.ilike(f"%{search}%"),
                    KnowledgePoint.hanzi.ilike(f"%{search}%"),
                )
            )

        query = select(KnowledgePoint).where(and_(*conditions)) if conditions else select(KnowledgePoint)
        query = query.order_by(KnowledgePoint.level, KnowledgePoint.kp_type)

        count_query = select(func.count(KnowledgePoint.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        result = await self.db.execute(query.offset(offset).limit(limit))
        items = list(result.scalars().all())

        return items, total

    async def get_knowledge_point(self, kp_id: uuid.UUID) -> KnowledgePoint | None:
        result = await self.db.execute(
            select(KnowledgePoint).where(KnowledgePoint.id == kp_id)
        )
        return result.scalar_one_or_none()

    async def create_knowledge_point(self, data: KnowledgePointCreate) -> KnowledgePoint:
        kp = KnowledgePoint(**data.model_dump())
        self.db.add(kp)
        await self.db.flush()
        return kp

    async def update_knowledge_point(self, kp_id: uuid.UUID, data: KnowledgePointUpdate) -> KnowledgePoint:
        kp = await self.get_knowledge_point(kp_id)
        if not kp:
            raise ValueError("知识点不存在")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(kp, key, value)
        await self.db.flush()
        return kp

    async def delete_knowledge_point(self, kp_id: uuid.UUID):
        kp = await self.get_knowledge_point(kp_id)
        if not kp:
            raise ValueError("知识点不存在")
        await self.db.delete(kp)
        await self.db.flush()

    async def create_relation(self, data: KnowledgeRelationCreate) -> KnowledgeRelation:
        relation = KnowledgeRelation(**data.model_dump())
        self.db.add(relation)
        await self.db.flush()
        return relation

    async def get_kp_relations(self, kp_id: uuid.UUID) -> dict:
        pred_result = await self.db.execute(
            select(KnowledgeRelation).where(KnowledgeRelation.successor_id == kp_id)
        )
        succ_result = await self.db.execute(
            select(KnowledgeRelation).where(KnowledgeRelation.predecessor_id == kp_id)
        )
        return {
            "predecessor_ids": [r.predecessor_id for r in pred_result.scalars().all()],
            "successor_ids": [r.successor_id for r in succ_result.scalars().all()],
        }

    async def list_lessons(
        self, level: int | None = None, lesson_type: str | None = None,
        page: int = 1, page_size: int = 20
    ) -> tuple[list[Lesson], int]:
        offset, limit = paginate(page, page_size)
        conditions = []

        if level:
            conditions.append(Lesson.level == level)
        if lesson_type:
            conditions.append(Lesson.lesson_type == lesson_type)

        query = select(Lesson)
        count_query = select(func.count(Lesson.id))
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        query = query.order_by(Lesson.level, Lesson.order_index)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        result = await self.db.execute(query.offset(offset).limit(limit))
        items = list(result.scalars().all())

        return items, total

    async def get_lesson(self, lesson_id: uuid.UUID) -> Lesson | None:
        result = await self.db.execute(select(Lesson).where(Lesson.id == lesson_id))
        return result.scalar_one_or_none()

    async def create_lesson(self, data: LessonCreate) -> Lesson:
        lesson = Lesson(**data.model_dump())
        self.db.add(lesson)
        await self.db.flush()
        return lesson

    async def list_scenes(
        self, level: int | None = None, category: str | None = None,
        page: int = 1, page_size: int = 20
    ) -> tuple[list[DialogueScene], int]:
        offset, limit = paginate(page, page_size)
        conditions = []

        if level:
            conditions.append(DialogueScene.level == level)
        if category:
            conditions.append(DialogueScene.scene_category == category)

        query = select(DialogueScene)
        count_query = select(func.count(DialogueScene.id))
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        result = await self.db.execute(query.offset(offset).limit(limit))
        items = list(result.scalars().all())

        return items, total

    async def create_scene(self, data: DialogueSceneCreate) -> DialogueScene:
        scene = DialogueScene(**data.model_dump())
        self.db.add(scene)
        await self.db.flush()
        return scene

    async def submit_record(self, user_id: uuid.UUID, data: LearningRecordCreate) -> LearningRecord:
        record = LearningRecord(user_id=user_id, **data.model_dump())
        self.db.add(record)
        await self.db.flush()

        await self._update_profile_on_activity(user_id, data)

        if data.target_id and data.record_type in (
            "pronunciation_practice", "vocab_quiz", "grammar_quiz"
        ):
            await self._update_mastery(user_id, data.target_id, data.score, data.detail)

        return record

    async def _update_profile_on_activity(self, user_id: uuid.UUID, data: LearningRecordCreate):
        from app.models import User, UserProfile
        from datetime import date

        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            return

        # Update total study time
        if data.duration_sec and data.duration_sec > 0:
            profile.total_study_sec += data.duration_sec

        # Update streak
        today = date.today()
        if profile.last_study_date != today:
            if profile.last_study_date and (today - profile.last_study_date).days == 1:
                profile.streak_days += 1
            elif profile.last_study_date and (today - profile.last_study_date).days > 1:
                profile.streak_days = 1
            else:
                profile.streak_days = max(1, profile.streak_days)
            profile.last_study_date = today

        # Update counters based on record type
        if data.record_type == "vocab_quiz":
            profile.total_practice_count += 1
            if data.score is not None and data.score >= 60:
                new_mastered = profile.vocab_mastered + 1
                profile.vocab_mastered = new_mastered
                # Recalculate level based on vocab
                if new_mastered >= 4000: profile.current_level = 8
                elif new_mastered >= 3000: profile.current_level = 7
                elif new_mastered >= 2200: profile.current_level = 6
                elif new_mastered >= 1500: profile.current_level = 5
                elif new_mastered >= 1000: profile.current_level = 4
                elif new_mastered >= 600: profile.current_level = 3
                elif new_mastered >= 300: profile.current_level = 2
        elif data.record_type == "pronunciation_practice":
            profile.total_practice_count += 1
            if data.score is not None:
                score_val = data.score
                if profile.speaking_accuracy is not None:
                    profile.speaking_accuracy = round((profile.speaking_accuracy * 0.7 + score_val * 0.3), 1)
                else:
                    profile.speaking_accuracy = round(score_val, 1)
        elif data.record_type == "dialogue_message":
            profile.total_dialogue_count += 1
        elif data.record_type == "lesson_complete":
            profile.total_lessons_completed += 1

        await self.db.flush()

    async def sync_profile_stats(self, user_id: uuid.UUID, stats: dict) -> UserProfile:
        from app.models import UserProfile

        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise ValueError("用户档案不存在")

        if "vocab_mastered" in stats:
            profile.vocab_mastered = max(profile.vocab_mastered, stats["vocab_mastered"])
        if "total_study_sec" in stats:
            profile.total_study_sec = max(profile.total_study_sec, stats["total_study_sec"])
        if "streak_days" in stats:
            profile.streak_days = max(profile.streak_days, stats["streak_days"])
        if "speaking_accuracy" in stats:
            profile.speaking_accuracy = stats["speaking_accuracy"]
        if "tone_accuracy" in stats:
            profile.tone_accuracy = stats["tone_accuracy"]
        if "grammar_accuracy" in stats:
            profile.grammar_accuracy = stats["grammar_accuracy"]
        if "listening_accuracy" in stats:
            profile.listening_accuracy = stats["listening_accuracy"]
        if "total_lessons_completed" in stats:
            profile.total_lessons_completed = max(profile.total_lessons_completed, stats["total_lessons_completed"])
        if "total_practice_count" in stats:
            profile.total_practice_count = max(profile.total_practice_count, stats["total_practice_count"])
        if "total_dialogue_count" in stats:
            profile.total_dialogue_count = max(profile.total_dialogue_count, stats["total_dialogue_count"])

        # Recalculate level based on vocab
        vm = profile.vocab_mastered
        if vm >= 4000: profile.current_level = 8
        elif vm >= 3000: profile.current_level = 7
        elif vm >= 2200: profile.current_level = 6
        elif vm >= 1500: profile.current_level = 5
        elif vm >= 1000: profile.current_level = 4
        elif vm >= 600: profile.current_level = 3
        elif vm >= 300: profile.current_level = 2

        await self.db.flush()
        return profile

    async def _update_mastery(
        self, user_id: uuid.UUID, kp_id: uuid.UUID,
        score: float | None, detail: dict | None
    ):
        result = await self.db.execute(
            select(KnowledgeMastery).where(
                and_(KnowledgeMastery.user_id == user_id, KnowledgeMastery.kp_id == kp_id)
            )
        )
        mastery = result.scalar_one_or_none()

        if not mastery:
            mastery = KnowledgeMastery(user_id=user_id, kp_id=kp_id)
            self.db.add(mastery)
            await self.db.flush()

        correct = (score or 0) >= 60.0
        quality = min(5, max(0, int((score or 0) / 20)))

        mastery.p_learned = bkt_update(
            mastery.p_learned, mastery.p_transit,
            mastery.p_guess, mastery.p_slip, correct
        )
        mastery.practice_count += 1
        mastery.last_practice_at = datetime.utcnow()

        if correct:
            mastery.consecutive_correct += 1
        else:
            mastery.consecutive_correct = 0

        new_ef, new_interval = sm2_update(
            mastery.ef_factor, quality, 1, mastery.consecutive_correct
        )
        mastery.ef_factor = new_ef
        mastery.next_review_at = datetime.utcnow() + timedelta(days=new_interval)

        await self.db.flush()

    async def get_records(
        self, user_id: uuid.UUID, record_type: str | None = None,
        from_date: datetime | None = None, to_date: datetime | None = None,
        page: int = 1, page_size: int = 20
    ) -> tuple[list[LearningRecord], int]:
        offset, limit = paginate(page, page_size)
        conditions = [LearningRecord.user_id == user_id]

        if record_type:
            conditions.append(LearningRecord.record_type == record_type)
        if from_date:
            conditions.append(LearningRecord.created_at >= from_date)
        if to_date:
            conditions.append(LearningRecord.created_at <= to_date)

        query = select(LearningRecord).where(and_(*conditions)).order_by(desc(LearningRecord.created_at))
        count_query = select(func.count(LearningRecord.id)).where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        result = await self.db.execute(query.offset(offset).limit(limit))
        items = list(result.scalars().all())

        return items, total

    async def get_review_queue(self, user_id: uuid.UUID, limit: int = 20) -> list[ReviewQueueItem]:
        now = datetime.utcnow()
        result = await self.db.execute(
            select(KnowledgeMastery)
            .where(
                and_(
                    KnowledgeMastery.user_id == user_id,
                    or_(
                        KnowledgeMastery.next_review_at.is_(None),
                        KnowledgeMastery.next_review_at <= now,
                    ),
                )
            )
            .order_by(KnowledgeMastery.next_review_at.asc().nulls_first())
            .limit(limit)
        )
        masteries = result.scalars().all()

        items = []
        for m in masteries:
            kp = await self.get_knowledge_point(m.kp_id)
            overdue = days_between(m.next_review_at, now) if m.next_review_at else 999
            items.append(ReviewQueueItem(
                mastery_id=m.id,
                kp_id=m.kp_id,
                kp_title=kp.title if kp else "未知",
                kp_type=kp.kp_type if kp else "unknown",
                p_learned=m.p_learned,
                ef_factor=m.ef_factor,
                next_review_at=m.next_review_at,
                days_overdue=overdue,
            ))

        return items

    async def get_user_masteries(self, user_id: uuid.UUID) -> list[KnowledgeMastery]:
        result = await self.db.execute(
            select(KnowledgeMastery).where(KnowledgeMastery.user_id == user_id)
        )
        return list(result.scalars().all())

    async def create_vocabulary(self, data: VocabularyCreate) -> Vocabulary:
        vocab = Vocabulary(**data.model_dump())
        self.db.add(vocab)
        await self.db.flush()
        return vocab
