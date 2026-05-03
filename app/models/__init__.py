import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, Text, Date, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


def new_uuid():
    return uuid.uuid4()


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class ContentStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True)
    wechat_unionid: Mapped[str | None] = mapped_column(String(64), unique=True)
    email: Mapped[str | None] = mapped_column(String(128), unique=True)
    nickname: Mapped[str | None] = mapped_column(String(50))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    password_hash: Mapped[str | None] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(20), default=UserRole.USER.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_login_ip: Mapped[str | None] = mapped_column(String(45))

    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False)
    ability_snapshots: Mapped[list["AbilitySnapshot"]] = relationship(back_populates="user")
    learning_records: Mapped[list["LearningRecord"]] = relationship(back_populates="user")
    knowledge_masteries: Mapped[list["KnowledgeMastery"]] = relationship(back_populates="user")
    agent_sessions: Mapped[list["AgentSession"]] = relationship(back_populates="user")
    activity_logs: Mapped[list["ActivityLog"]] = relationship(back_populates="user")
    content_versions: Mapped[list["ContentVersion"]] = relationship(back_populates="creator")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    native_language: Mapped[str | None] = mapped_column(String(30))
    self_eval_level: Mapped[int | None] = mapped_column(Integer)
    current_level: Mapped[int] = mapped_column(Integer, default=1)
    total_study_sec: Mapped[int] = mapped_column(Integer, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_study_date: Mapped[datetime | None] = mapped_column(Date)
    vocab_mastered: Mapped[int] = mapped_column(Integer, default=0)
    tone_accuracy: Mapped[float | None] = mapped_column(Float)
    grammar_accuracy: Mapped[float | None] = mapped_column(Float)
    listening_accuracy: Mapped[float | None] = mapped_column(Float)
    speaking_accuracy: Mapped[float | None] = mapped_column(Float)
    total_lessons_completed: Mapped[int] = mapped_column(Integer, default=0)
    total_practice_count: Mapped[int] = mapped_column(Integer, default=0)
    total_dialogue_count: Mapped[int] = mapped_column(Integer, default=0)
    preferred_tone_id: Mapped[str | None] = mapped_column(String(20))
    weak_tone_ids: Mapped[list | None] = mapped_column(ARRAY(String))
    learning_preference: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="profile")

    __table_args__ = (
        CheckConstraint("current_level BETWEEN 1 AND 8", name="ck_profile_level"),
    )


class AbilitySnapshot(Base):
    __tablename__ = "ability_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    pronunciation: Mapped[float] = mapped_column(Float)
    vocabulary: Mapped[float] = mapped_column(Float)
    grammar: Mapped[float] = mapped_column(Float)
    listening: Mapped[float] = mapped_column(Float)
    speaking: Mapped[float] = mapped_column(Float)
    culture: Mapped[float] = mapped_column(Float)
    overall_score: Mapped[float] = mapped_column(Float)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="ability_snapshots")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    phone: Mapped[str] = mapped_column(String(20), index=True)
    code: Mapped[str] = mapped_column(String(10))
    code_type: Mapped[str] = mapped_column(String(20))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class KnowledgePoint(Base):
    __tablename__ = "knowledge_points"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    kp_type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    level: Mapped[int] = mapped_column(Integer)
    pinyin: Mapped[str | None] = mapped_column(String(100))
    ipa: Mapped[str | None] = mapped_column(String(100))
    hanzi: Mapped[str | None] = mapped_column(String(500))
    audio_url: Mapped[str | None] = mapped_column(String(500))
    image_url: Mapped[str | None] = mapped_column(String(500))
    metadata: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default=ContentStatus.PUBLISHED.value)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    mastery_rate: Mapped[float] = mapped_column(Float, default=0.0)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vocabulary: Mapped["Vocabulary | None"] = relationship(back_populates="knowledge_point", uselist=False)
    predecessors: Mapped[list["KnowledgeRelation"]] = relationship(
        foreign_keys="KnowledgeRelation.successor_id", back_populates="successor"
    )
    successors: Mapped[list["KnowledgeRelation"]] = relationship(
        foreign_keys="KnowledgeRelation.predecessor_id", back_populates="predecessor"
    )
    content_versions: Mapped[list["ContentVersion"]] = relationship(back_populates="knowledge_point")

    __table_args__ = (
        CheckConstraint("level BETWEEN 1 AND 8", name="ck_kp_level"),
    )


class KnowledgeRelation(Base):
    __tablename__ = "knowledge_relations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    predecessor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_points.id"))
    successor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_points.id"))
    relation_type: Mapped[str] = mapped_column(String(20), default="prerequisite")

    predecessor: Mapped["KnowledgePoint"] = relationship(foreign_keys=[predecessor_id], back_populates="successors")
    successor: Mapped["KnowledgePoint"] = relationship(foreign_keys=[successor_id], back_populates="predecessors")

    __table_args__ = (
        UniqueConstraint("predecessor_id", "successor_id", name="uq_knowledge_relation"),
    )


class Vocabulary(Base):
    __tablename__ = "vocabularies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    kp_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_points.id"), unique=True)
    word_category: Mapped[str | None] = mapped_column(String(30))
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    example_sentences: Mapped[list | None] = mapped_column(JSONB)
    image_url: Mapped[str | None] = mapped_column(String(500))
    audio_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    knowledge_point: Mapped["KnowledgePoint"] = relationship(back_populates="vocabulary")


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    level: Mapped[int] = mapped_column(Integer)
    kp_ids: Mapped[list | None] = mapped_column(ARRAY(UUID(as_uuid=True)))
    lesson_type: Mapped[str] = mapped_column(String(20))
    duration_est: Mapped[int | None] = mapped_column(Integer)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))
    content_json: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default=ContentStatus.PUBLISHED.value)
    completion_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    content_versions: Mapped[list["ContentVersion"]] = relationship(back_populates="lesson")

    __table_args__ = (
        CheckConstraint("level BETWEEN 1 AND 8", name="ck_lesson_level"),
    )


class DialogueScene(Base):
    __tablename__ = "dialogue_scenes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(String(100))
    scene_category: Mapped[str | None] = mapped_column(String(30))
    level: Mapped[int] = mapped_column(Integer)
    target_vocabs: Mapped[list | None] = mapped_column(ARRAY(UUID(as_uuid=True)))
    target_grammar: Mapped[list | None] = mapped_column(ARRAY(UUID(as_uuid=True)))
    dialogues: Mapped[list | None] = mapped_column(JSONB)
    mode: Mapped[str] = mapped_column(String(20), default="guided")
    background_image_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default=ContentStatus.PUBLISHED.value)
    play_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    content_versions: Mapped[list["ContentVersion"]] = relationship(back_populates="dialogue_scene")

    __table_args__ = (
        CheckConstraint("level BETWEEN 1 AND 8", name="ck_scene_level"),
    )


class LearningRecord(Base):
    __tablename__ = "learning_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    record_type: Mapped[str] = mapped_column(String(30))
    target_type: Mapped[str | None] = mapped_column(String(20))
    target_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    score: Mapped[float | None] = mapped_column(Float)
    duration_sec: Mapped[int | None] = mapped_column(Integer)
    detail: Mapped[dict | None] = mapped_column(JSONB)
    device_info: Mapped[dict | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="learning_records")


class KnowledgeMastery(Base):
    __tablename__ = "knowledge_mastery"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    kp_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_points.id"))
    p_learned: Mapped[float] = mapped_column(Float, default=0.0)
    p_transit: Mapped[float] = mapped_column(Float, default=0.3)
    p_guess: Mapped[float] = mapped_column(Float, default=0.2)
    p_slip: Mapped[float] = mapped_column(Float, default=0.1)
    last_practice_at: Mapped[datetime | None] = mapped_column(DateTime)
    practice_count: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_correct: Mapped[int] = mapped_column(Integer, default=0)
    ef_factor: Mapped[float] = mapped_column(Float, default=2.5)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="knowledge_masteries")

    __table_args__ = (
        UniqueConstraint("user_id", "kp_id", name="uq_user_kp_mastery"),
    )


class AgentSession(Base):
    __tablename__ = "agent_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    session_type: Mapped[str] = mapped_column(String(30), default="free_chat")
    context_ref: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="active")
    summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped["User"] = relationship(back_populates="agent_sessions")
    messages: Mapped[list["AgentMessage"]] = relationship(back_populates="session")


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_sessions.id"))
    role: Mapped[str] = mapped_column(String(10))
    content_type: Mapped[str] = mapped_column(String(20), default="text")
    content: Mapped[str | None] = mapped_column(Text)
    audio_url: Mapped[str | None] = mapped_column(String(500))
    tool_name: Mapped[str | None] = mapped_column(String(50))
    tool_params: Mapped[dict | None] = mapped_column(JSONB)
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["AgentSession"] = relationship(back_populates="messages")


class ContentVersion(Base):
    __tablename__ = "content_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    content_type: Mapped[str] = mapped_column(String(30))
    content_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    kp_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_points.id"))
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("lessons.id"))
    dialogue_scene_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("dialogue_scenes.id"))
    version: Mapped[int] = mapped_column(Integer, default=1)
    change_summary: Mapped[str | None] = mapped_column(Text)
    content_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default=ContentStatus.DRAFT.value)
    creator_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    creator: Mapped["User"] = relationship(back_populates="content_versions")
    knowledge_point: Mapped["KnowledgePoint"] = relationship(back_populates="content_versions")
    lesson: Mapped["Lesson"] = relationship(back_populates="content_versions")
    dialogue_scene: Mapped["DialogueScene"] = relationship(back_populates="content_versions")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(50))
    resource_type: Mapped[str | None] = mapped_column(String(30))
    resource_id: Mapped[str | None] = mapped_column(String(100))
    detail: Mapped[dict | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="activity_logs")


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    key: Mapped[str] = mapped_column(String(100), unique=True)
    value: Mapped[dict | None] = mapped_column(JSONB)
    description: Mapped[str | None] = mapped_column(String(500))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
