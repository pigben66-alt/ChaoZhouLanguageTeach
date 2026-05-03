import uuid
from datetime import datetime
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AgentSession, AgentMessage
from app.schemas.agent import AgentSessionCreate, AgentMessageCreate
from app.utils.helpers import paginate, calc_total_pages


class AgentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, user_id: uuid.UUID, data: AgentSessionCreate) -> AgentSession:
        session = AgentSession(
            user_id=user_id,
            session_type=data.session_type,
            context_ref=data.context_ref,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_session(self, session_id: uuid.UUID) -> AgentSession | None:
        result = await self.db.execute(
            select(AgentSession).where(AgentSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self, user_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> tuple[list[AgentSession], int]:
        offset, limit = paginate(page, page_size)

        query = (
            select(AgentSession)
            .where(AgentSession.user_id == user_id)
            .order_by(desc(AgentSession.created_at))
        )
        count_query = select(AgentSession).where(AgentSession.user_id == user_id)

        total_result = await self.db.execute(count_query)
        total = len(list(total_result.scalars().all()))

        result = await self.db.execute(query.offset(offset).limit(limit))
        items = list(result.scalars().all())

        return items, total

    async def get_session_messages(
        self, session_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> tuple[list[AgentMessage], int]:
        offset, limit = paginate(page, page_size)

        query = (
            select(AgentMessage)
            .where(AgentMessage.session_id == session_id)
            .order_by(AgentMessage.created_at)
        )
        count_query = select(AgentMessage).where(AgentMessage.session_id == session_id)

        total_result = await self.db.execute(count_query)
        total = len(list(total_result.scalars().all()))

        result = await self.db.execute(query.offset(offset).limit(limit))
        items = list(result.scalars().all())

        return items, total

    async def add_message(
        self, session_id: uuid.UUID, role: str, content: str,
        content_type: str = "text", tool_name: str | None = None,
        tool_params: dict | None = None, tokens_used: int | None = None,
        latency_ms: int | None = None,
    ) -> AgentMessage:
        message = AgentMessage(
            session_id=session_id,
            role=role,
            content_type=content_type,
            content=content,
            tool_name=tool_name,
            tool_params=tool_params,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )
        self.db.add(message)
        await self.db.flush()
        return message

    async def close_session(self, session_id: uuid.UUID, summary: str | None = None):
        session = await self.get_session(session_id)
        if not session:
            raise ValueError("会话不存在")

        session.status = "closed"
        session.closed_at = datetime.utcnow()
        if summary:
            session.summary = summary
        await self.db.flush()
        return session
