import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class KnowledgePointResponse(BaseModel):
    id: uuid.UUID
    kp_type: str
    title: str
    description: str | None
    level: int
    pinyin: str | None
    ipa: str | None
    hanzi: str | None
    metadata: dict | None

    class Config:
        from_attributes = True


class KnowledgePointDetail(KnowledgePointResponse):
    vocabulary: "VocabularyResponse | None" = None
    predecessor_ids: list[uuid.UUID] = []
    successor_ids: list[uuid.UUID] = []


class KnowledgePointCreate(BaseModel):
    kp_type: str = Field(max_length=20)
    title: str = Field(max_length=100)
    description: str | None = None
    level: int = Field(ge=1, le=8)
    pinyin: str | None = Field(default=None, max_length=50)
    ipa: str | None = Field(default=None, max_length=50)
    hanzi: str | None = Field(default=None, max_length=200)
    metadata: dict | None = None


class KnowledgePointUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=100)
    description: str | None = None
    level: int | None = Field(default=None, ge=1, le=8)
    pinyin: str | None = Field(default=None, max_length=50)
    ipa: str | None = Field(default=None, max_length=50)
    hanzi: str | None = Field(default=None, max_length=200)
    metadata: dict | None = None


class KnowledgeRelationCreate(BaseModel):
    predecessor_id: uuid.UUID
    successor_id: uuid.UUID
    relation_type: str = "prerequisite"


class VocabularyResponse(BaseModel):
    id: uuid.UUID
    kp_id: uuid.UUID
    word_category: str | None
    difficulty: int
    example_sentences: list | None
    image_url: str | None

    class Config:
        from_attributes = True


class VocabularyCreate(BaseModel):
    kp_id: uuid.UUID
    word_category: str | None = Field(default=None, max_length=30)
    difficulty: int = Field(default=1, ge=1, le=5)
    example_sentences: list | None = None
    image_url: str | None = Field(default=None, max_length=500)


class LessonResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    level: int
    kp_ids: list[uuid.UUID] | None
    lesson_type: str
    duration_est: int | None
    order_index: int

    class Config:
        from_attributes = True


class LessonCreate(BaseModel):
    title: str = Field(max_length=100)
    description: str | None = None
    level: int = Field(ge=1, le=8)
    kp_ids: list[uuid.UUID] | None = None
    lesson_type: str = Field(max_length=20)
    duration_est: int | None = None
    order_index: int = 0


class DialogueSceneResponse(BaseModel):
    id: uuid.UUID
    title: str
    scene_category: str | None
    level: int
    target_vocabs: list[uuid.UUID] | None
    target_grammar: list[uuid.UUID] | None
    dialogues: list | None
    mode: str

    class Config:
        from_attributes = True


class DialogueSceneCreate(BaseModel):
    title: str = Field(max_length=100)
    scene_category: str | None = Field(default=None, max_length=30)
    level: int = Field(ge=1, le=8)
    target_vocabs: list[uuid.UUID] | None = None
    target_grammar: list[uuid.UUID] | None = None
    dialogues: list | None = None
    mode: str = "guided"


class LearningRecordCreate(BaseModel):
    record_type: str = Field(max_length=30)
    target_type: str | None = Field(default=None, max_length=20)
    target_id: uuid.UUID | None = None
    score: float | None = None
    duration_sec: int | None = None
    detail: dict | None = None
    device_info: dict | None = None


class LearningRecordResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    record_type: str
    target_type: str | None
    target_id: uuid.UUID | None
    score: float | None
    duration_sec: int | None
    detail: dict | None
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeMasteryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    kp_id: uuid.UUID
    p_learned: float
    practice_count: int
    consecutive_correct: int
    ef_factor: float
    next_review_at: datetime | None
    last_practice_at: datetime | None

    class Config:
        from_attributes = True


class ReviewQueueItem(BaseModel):
    mastery_id: uuid.UUID
    kp_id: uuid.UUID
    kp_title: str
    kp_type: str
    p_learned: float
    ef_factor: float
    next_review_at: datetime | None
    days_overdue: int


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
