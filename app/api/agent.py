import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.services.agent_service import AgentService
from app.services.user_service import UserService
from app.agent.engine import AgentEngine
from app.agent.toolbox import Toolbox
from app.agent.memory import MemoryManager
from app.llm.router import ModelRouter
from app.schemas.agent import (
    AgentSessionCreate, AgentSessionResponse, AgentSessionDetail,
    AgentMessageCreate, AgentMessageResponse,
)
from app.utils.helpers import calc_total_pages

router = APIRouter(prefix="/api/v1/agent", tags=["AI伴学Agent"])


def get_agent_engine(db: AsyncSession = Depends(get_db)) -> AgentEngine:
    router = ModelRouter()
    toolbox = Toolbox(db)
    memory = MemoryManager(db)
    return AgentEngine(router, toolbox, memory)


@router.post("/sessions", response_model=AgentSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: AgentSessionCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = AgentService(db)
    return await service.create_session(user_id, data)


@router.get("/sessions")
async def list_sessions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = AgentService(db)
    items, total = await service.list_sessions(user_id, page, page_size)
    return {
        "items": [AgentSessionResponse.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": calc_total_pages(total, page_size),
    }


@router.get("/sessions/{session_id}", response_model=AgentSessionDetail)
async def get_session(
    session_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = AgentService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    if session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此会话")

    messages, _ = await service.get_session_messages(session_id)
    return AgentSessionDetail(
        id=session.id, user_id=session.user_id, session_type=session.session_type,
        context_ref=session.context_ref, status=session.status, summary=session.summary,
        created_at=session.created_at, closed_at=session.closed_at,
        messages=[AgentMessageResponse.model_validate(m) for m in messages],
    )


@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = AgentService(db)
    session = await service.get_session(session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此会话")

    items, total = await service.get_session_messages(session_id, page, page_size)
    return {
        "items": [AgentMessageResponse.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": calc_total_pages(total, page_size),
    }


@router.post("/sessions/{session_id}/chat")
async def chat_with_agent(
    session_id: uuid.UUID,
    data: AgentMessageCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    engine: AgentEngine = Depends(get_agent_engine),
):
    service = AgentService(db)
    session = await service.get_session(session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此会话")

    await service.add_message(session_id, "user", data.content, data.content_type)

    async def event_stream():
        full_response = ""
        async for chunk in engine.process_message(user_id, session_id, data.content):
            if chunk["type"] == "text":
                full_response += chunk["payload"]["text"]
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

        await service.add_message(
            session_id, "assistant", full_response,
            tokens_used=len(full_response),
        )
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/sessions/{session_id}/close")
async def close_session(
    session_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = AgentService(db)
    session = await service.get_session(session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此会话")

    return await service.close_session(session_id)
