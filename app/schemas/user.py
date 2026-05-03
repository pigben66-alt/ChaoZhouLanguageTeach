import uuid
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class UserRegister(BaseModel):
    phone: str = Field(max_length=20)
    password: str = Field(min_length=6, max_length=128)
    nickname: str | None = Field(default=None, max_length=50)
    verification_code: str = Field(min_length=4, max_length=10)


class UserLogin(BaseModel):
    phone: str = Field(max_length=20)
    password: str = Field(min_length=6, max_length=128)


class SendVerificationCodeRequest(BaseModel):
    phone: str = Field(max_length=20)
    code_type: str = Field(default="register", max_length=20)


class VerifyCodeRequest(BaseModel):
    phone: str = Field(max_length=20)
    code: str = Field(min_length=4, max_length=10)
    code_type: str = Field(max_length=20)


class ForgotPasswordRequest(BaseModel):
    phone: str = Field(max_length=20)
    verification_code: str = Field(min_length=4, max_length=10)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=128)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserInfoResponse"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserInfoResponse(BaseModel):
    id: uuid.UUID
    phone: str | None
    nickname: str | None
    avatar_url: str | None
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    native_language: str | None
    self_eval_level: int | None
    current_level: int
    total_study_sec: int
    streak_days: int
    last_study_date: datetime | None
    vocab_mastered: int
    tone_accuracy: float | None
    grammar_accuracy: float | None
    listening_accuracy: float | None
    speaking_accuracy: float | None
    total_lessons_completed: int
    total_practice_count: int
    total_dialogue_count: int

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    nickname: str | None = Field(default=None, max_length=50)
    avatar_url: str | None = Field(default=None, max_length=500)
    native_language: str | None = Field(default=None, max_length=30)
    self_eval_level: int | None = Field(default=None, ge=1, le=8)


class UserProgressResponse(BaseModel):
    current_level: int
    total_study_sec: int
    streak_days: int
    vocab_mastered: int
    tone_accuracy: float | None
    grammar_accuracy: float | None
    listening_accuracy: float | None
    speaking_accuracy: float | None
    total_lessons_completed: int
    total_practice_count: int
    total_dialogue_count: int

    class Config:
        from_attributes = True


class AbilitySnapshotResponse(BaseModel):
    id: uuid.UUID
    pronunciation: float
    vocabulary: float
    grammar: float
    listening: float
    speaking: float
    culture: float
    overall_score: float
    evaluated_at: datetime

    class Config:
        from_attributes = True


class ActivityLogResponse(BaseModel):
    id: uuid.UUID
    action: str
    resource_type: str | None
    resource_id: str | None
    detail: dict | None
    ip_address: str | None
    created_at: datetime

    class Config:
        from_attributes = True
