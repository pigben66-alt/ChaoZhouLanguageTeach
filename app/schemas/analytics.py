from datetime import date
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    current_level: int
    total_study_hours: float
    streak_days: int
    vocab_mastered: int
    vocab_target: int
    pronunciation_accuracy: float
    weekly_growth: float
    lessons_completed: int
    total_lessons: int


class HeatmapData(BaseModel):
    date: str
    minutes: int
    level: int


class RadarData(BaseModel):
    dimensions: list[str]
    values: list[float]
    max_value: float = 100.0


class TrendData(BaseModel):
    labels: list[str]
    datasets: list[dict]


class WeaknessItem(BaseModel):
    kp_id: str
    title: str
    kp_type: str
    accuracy: float
    practice_count: int
    trend: str


class ReportResponse(BaseModel):
    report_url: str
    generated_at: str
    period: str
