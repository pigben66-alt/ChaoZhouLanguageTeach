import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.services.learning_service import LearningService
from app.schemas.learning import (
    KnowledgePointResponse, KnowledgePointDetail, KnowledgePointCreate, KnowledgePointUpdate,
    KnowledgeRelationCreate, VocabularyResponse, VocabularyCreate,
    LessonResponse, LessonCreate, DialogueSceneResponse, DialogueSceneCreate,
    LearningRecordCreate, LearningRecordResponse, KnowledgeMasteryResponse,
    ReviewQueueItem, PaginatedResponse,
)
from app.utils.helpers import calc_total_pages

router = APIRouter(prefix="/api/v1/learning", tags=["学习"])


@router.get("/knowledge-points")
async def list_knowledge_points(
    kp_type: str | None = Query(default=None),
    level: int | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = LearningService(db)
    items, total = await service.list_knowledge_points(kp_type, level, search, page, page_size)
    return {
        "items": [KnowledgePointResponse.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": calc_total_pages(total, page_size),
    }


@router.get("/knowledge-points/{kp_id}", response_model=KnowledgePointDetail)
async def get_knowledge_point(kp_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = LearningService(db)
    kp = await service.get_knowledge_point(kp_id)
    if not kp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识点不存在")

    relations = await service.get_kp_relations(kp_id)

    vocab = None
    if kp.kp_type == "vocabulary":
        vocab_result = await db.execute(
            __import__("sqlalchemy").select(
                __import__("app.models", fromlist=["Vocabulary"]).Vocabulary
            ).where(
                __import__("app.models", fromlist=["Vocabulary"]).Vocabulary.kp_id == kp_id
            )
        )
        vocab = vocab_result.scalar_one_or_none()

    return KnowledgePointDetail(
        id=kp.id, kp_type=kp.kp_type, title=kp.title, description=kp.description,
        level=kp.level, pinyin=kp.pinyin, ipa=kp.ipa, hanzi=kp.hanzi,
        metadata=kp.metadata,
        vocabulary=VocabularyResponse.model_validate(vocab) if vocab else None,
        predecessor_ids=relations["predecessor_ids"],
        successor_ids=relations["successor_ids"],
    )


@router.post("/knowledge-points", response_model=KnowledgePointResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_point(
    data: KnowledgePointCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = LearningService(db)
    return await service.create_knowledge_point(data)


@router.put("/knowledge-points/{kp_id}", response_model=KnowledgePointResponse)
async def update_knowledge_point(
    kp_id: uuid.UUID, data: KnowledgePointUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = LearningService(db)
    try:
        return await service.update_knowledge_point(kp_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/knowledge-points/{kp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_point(
    kp_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = LearningService(db)
    try:
        await service.delete_knowledge_point(kp_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/knowledge-relations", status_code=status.HTTP_201_CREATED)
async def create_knowledge_relation(
    data: KnowledgeRelationCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = LearningService(db)
    return await service.create_relation(data)


@router.get("/lessons")
async def list_lessons(
    level: int | None = Query(default=None),
    lesson_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = LearningService(db)
    items, total = await service.list_lessons(level, lesson_type, page, page_size)
    return {
        "items": [LessonResponse.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": calc_total_pages(total, page_size),
    }


@router.get("/lessons/{lesson_id}", response_model=LessonResponse)
async def get_lesson(lesson_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = LearningService(db)
    lesson = await service.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
    return lesson


@router.post("/lessons", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    data: LessonCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = LearningService(db)
    return await service.create_lesson(data)


@router.get("/scenes")
async def list_scenes(
    level: int | None = Query(default=None),
    category: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = LearningService(db)
    items, total = await service.list_scenes(level, category, page, page_size)
    return {
        "items": [DialogueSceneResponse.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": calc_total_pages(total, page_size),
    }


@router.post("/scenes", response_model=DialogueSceneResponse, status_code=status.HTTP_201_CREATED)
async def create_scene(
    data: DialogueSceneCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = LearningService(db)
    return await service.create_scene(data)


@router.post("/records", response_model=LearningRecordResponse, status_code=status.HTTP_201_CREATED)
async def submit_record(
    data: LearningRecordCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = LearningService(db)
    return await service.submit_record(user_id, data)


@router.post("/sync-profile")
async def sync_profile_stats(
    stats: dict,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = LearningService(db)
    try:
        profile = await service.sync_profile_stats(user_id, stats)
        return {
            "message": "数据同步成功",
            "current_level": profile.current_level,
            "vocab_mastered": profile.vocab_mastered,
            "total_study_sec": profile.total_study_sec,
            "streak_days": profile.streak_days,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/records")
async def get_records(
    record_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = LearningService(db)
    items, total = await service.get_records(user_id, record_type, page=page, page_size=page_size)
    return {
        "items": [LearningRecordResponse.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": calc_total_pages(total, page_size),
    }


@router.get("/review-queue")
async def get_review_queue(
    limit: int = Query(default=20, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = LearningService(db)
    items = await service.get_review_queue(user_id, limit)
    return {"items": items, "total": len(items)}


@router.get("/masteries")
async def get_masteries(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = LearningService(db)
    items = await service.get_user_masteries(user_id)
    return {"items": [KnowledgeMasteryResponse.model_validate(item) for item in items]}


@router.post("/vocabularies", response_model=VocabularyResponse, status_code=status.HTTP_201_CREATED)
async def create_vocabulary(
    data: VocabularyCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = LearningService(db)
    return await service.create_vocabulary(data)
