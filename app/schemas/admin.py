import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class AdminUserResponse(BaseModel):
    id: uuid.UUID
    phone: str | None
    nickname: str | None
    avatar_url: str | None
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: datetime | None

    class Config:
        from_attributes = True


class AdminUserDetail(AdminUserResponse):
    profile: "AdminUserProfileResponse | None" = None
    stats: "AdminUserStatsResponse" = None


class AdminUserProfileResponse(BaseModel):
    current_level: int
    total_study_sec: int
    streak_days: int
    vocab_mastered: int
    total_lessons_completed: int
    total_practice_count: int

    class Config:
        from_attributes = True


class AdminUserStatsResponse(BaseModel):
    total_study_hours: float
    avg_daily_study_minutes: float
    avg_score: float
    total_sessions: int
    active_days: int
    dominant_learn_type: str | None

    class Config:
        from_attributes = True


class AdminUpdateUserRole(BaseModel):
    user_id: uuid.UUID
    role: str = Field(ge=1, le=50)


class AdminToggleUserStatus(BaseModel):
    user_id: uuid.UUID
    is_active: bool


class AdminContentPublishRequest(BaseModel):
    content_type: str = Field(max_length=30)
    content_id: uuid.UUID
    action: str = Field(max_length=20)


class AdminContentVersionResponse(BaseModel):
    id: uuid.UUID
    content_type: str
    content_id: uuid.UUID | None
    version: int
    change_summary: str | None
    status: str
    creator_id: uuid.UUID | None
    published_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class AdminActivityLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    user_nickname: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    ip_address: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AdminSystemStatsResponse(BaseModel):
    total_users: int
    active_users_today: int
    active_users_week: int
    total_study_records: int
    today_study_records: int
    avg_study_score: float
    total_content_items: int
    published_content_items: int
    system_uptime: str


class AdminLearningTrendResponse(BaseModel):
    date: str
    new_users: int
    active_users: int
    study_records: int
    avg_score: float


class AdminContentStatsResponse(BaseModel):
    kp_count: int
    kp_published: int
    vocab_count: int
    lesson_count: int
    lesson_published: int
    scene_count: int
    scene_published: int


class AdminDashboardResponse(BaseModel):
    system_stats: AdminSystemStatsResponse
    content_stats: AdminContentStatsResponse
    learning_trends: list[AdminLearningTrendResponse]
    recent_activities: list[AdminActivityLogResponse]
    top_learners: list[AdminUserResponse]
