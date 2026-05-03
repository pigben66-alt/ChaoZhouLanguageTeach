import uuid
from datetime import datetime, date, timedelta
from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import LearningRecord, KnowledgeMastery, UserProfile, AbilitySnapshot, KnowledgePoint
from app.schemas.analytics import (
    DashboardSummary, HeatmapData, RadarData, TrendData, WeaknessItem,
)


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_summary(self, user_id: uuid.UUID) -> DashboardSummary:
        profile_result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()

        total_sec = profile.total_study_sec if profile else 0
        current_level = profile.current_level if profile else 1

        level_vocab_targets = {1: 100, 2: 300, 3: 600, 4: 1000, 5: 1500, 6: 2200, 7: 3000, 8: 4000}

        records_count = await self.db.execute(
            select(func.count(LearningRecord.id)).where(LearningRecord.user_id == user_id)
        )
        total_records = records_count.scalar() or 0

        lessons_count = await self.db.execute(
            select(func.count(LearningRecord.id)).where(
                and_(
                    LearningRecord.user_id == user_id,
                    LearningRecord.record_type == "lesson_complete",
                )
            )
        )
        lessons_completed = lessons_count.scalar() or 0

        week_ago = datetime.utcnow() - timedelta(days=7)
        week_records = await self.db.execute(
            select(func.count(LearningRecord.id)).where(
                and_(
                    LearningRecord.user_id == user_id,
                    LearningRecord.created_at >= week_ago,
                )
            )
        )
        week_count = week_records.scalar() or 0

        two_weeks_ago = datetime.utcnow() - timedelta(days=14)
        prev_week_records = await self.db.execute(
            select(func.count(LearningRecord.id)).where(
                and_(
                    LearningRecord.user_id == user_id,
                    LearningRecord.created_at >= two_weeks_ago,
                    LearningRecord.created_at < week_ago,
                )
            )
        )
        prev_week_count = prev_week_records.scalar() or 1

        weekly_growth = round(((week_count - prev_week_count) / max(1, prev_week_count)) * 100, 1)

        avg_score_result = await self.db.execute(
            select(func.avg(LearningRecord.score)).where(
                and_(
                    LearningRecord.user_id == user_id,
                    LearningRecord.score.isnot(None),
                )
            )
        )
        avg_score = avg_score_result.scalar() or 0

        return DashboardSummary(
            current_level=current_level,
            total_study_hours=round(total_sec / 3600, 1),
            streak_days=profile.streak_days if profile else 0,
            vocab_mastered=profile.vocab_mastered if profile else 0,
            vocab_target=level_vocab_targets.get(current_level, 1000),
            pronunciation_accuracy=round(float(avg_score), 1),
            weekly_growth=weekly_growth,
            lessons_completed=lessons_completed,
            total_lessons=total_records,
        )

    async def get_heatmap(self, user_id: uuid.UUID, month: str | None = None) -> list[HeatmapData]:
        if month:
            year, m = map(int, month.split("-"))
        else:
            today = date.today()
            year, m = today.year, today.month

        start_date = date(year, m, 1)
        if m == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, m + 1, 1)

        result = await self.db.execute(
            select(
                func.date(LearningRecord.created_at).label("study_date"),
                func.sum(LearningRecord.duration_sec).label("total_sec"),
                func.count(LearningRecord.id).label("record_count"),
            )
            .where(
                and_(
                    LearningRecord.user_id == user_id,
                    LearningRecord.created_at >= start_date,
                    LearningRecord.created_at < end_date,
                )
            )
            .group_by(func.date(LearningRecord.created_at))
        )

        data = []
        for row in result:
            minutes = (row.total_sec or 0) // 60
            level = 0
            if minutes > 120:
                level = 4
            elif minutes > 60:
                level = 3
            elif minutes > 30:
                level = 2
            elif minutes > 0:
                level = 1

            data.append(HeatmapData(
                date=str(row.study_date),
                minutes=minutes,
                level=level,
            ))

        return data

    async def get_radar(self, user_id: uuid.UUID) -> RadarData:
        result = await self.db.execute(
            select(AbilitySnapshot)
            .where(AbilitySnapshot.user_id == user_id)
            .order_by(AbilitySnapshot.evaluated_at.desc())
            .limit(1)
        )
        snapshot = result.scalar_one_or_none()

        if snapshot:
            return RadarData(
                dimensions=["发音", "词汇", "语法", "听力", "口语", "文化"],
                values=[
                    snapshot.pronunciation,
                    snapshot.vocabulary,
                    snapshot.grammar,
                    snapshot.listening,
                    snapshot.speaking,
                    snapshot.culture,
                ],
            )
        return RadarData(
            dimensions=["发音", "词汇", "语法", "听力", "口语", "文化"],
            values=[72, 68, 55, 60, 65, 45],
        )

    async def get_trend(self, user_id: uuid.UUID, metric: str = "score", period: str = "weekly") -> TrendData:
        days = 30 if period == "monthly" else 7
        start_date = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(
                func.date(LearningRecord.created_at).label("d"),
                func.avg(LearningRecord.score).label("avg_score"),
                func.sum(LearningRecord.duration_sec).label("total_sec"),
                func.count(LearningRecord.id).label("cnt"),
            )
            .where(
                and_(
                    LearningRecord.user_id == user_id,
                    LearningRecord.created_at >= start_date,
                )
            )
            .group_by(func.date(LearningRecord.created_at))
            .order_by(func.date(LearningRecord.created_at))
        )

        labels = []
        scores = []
        durations = []
        counts = []

        for row in result:
            labels.append(str(row.d))
            scores.append(round(float(row.avg_score or 0), 1))
            durations.append(round((row.total_sec or 0) / 60, 1))
            counts.append(row.cnt)

        datasets = []
        if metric == "score":
            datasets.append({"label": "平均得分", "data": scores})
        elif metric == "duration":
            datasets.append({"label": "学习时长(分钟)", "data": durations})
        elif metric == "count":
            datasets.append({"label": "练习次数", "data": counts})
        else:
            datasets.append({"label": "平均得分", "data": scores})
            datasets.append({"label": "学习时长(分钟)", "data": durations})

        return TrendData(labels=labels, datasets=datasets)

    async def get_weakness(self, user_id: uuid.UUID, top_n: int = 10) -> list[WeaknessItem]:
        result = await self.db.execute(
            select(KnowledgeMastery)
            .where(KnowledgeMastery.user_id == user_id)
            .order_by(KnowledgeMastery.p_learned.asc())
            .limit(top_n)
        )
        masteries = result.scalars().all()

        items = []
        for m in masteries:
            kp_result = await self.db.execute(
                select(KnowledgePoint).where(KnowledgePoint.id == m.kp_id)
            )
            kp = kp_result.scalar_one_or_none()

            accuracy = round(m.p_learned * 100, 1)
            trend = "down" if accuracy < 50 else ("up" if accuracy > 70 else "stable")

            items.append(WeaknessItem(
                kp_id=str(m.kp_id),
                title=kp.title if kp else "未知",
                kp_type=kp.kp_type if kp else "unknown",
                accuracy=accuracy,
                practice_count=m.practice_count,
                trend=trend,
            ))

        return items
