import uuid
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.agent_service import AgentService
from app.services.user_service import UserService


class MemoryManager:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent_service = AgentService(db)
        self.user_service = UserService(db)
        self._session_cache: dict[str, dict] = {}

    async def get_context(self, user_id: uuid.UUID, session_id: uuid.UUID) -> dict:
        cache_key = str(session_id)
        if cache_key in self._session_cache:
            return self._session_cache[cache_key]

        messages, _ = await self.agent_service.get_session_messages(session_id, page_size=20)

        history = []
        for msg in messages:
            history.append({
                "role": msg.role,
                "content": msg.content,
            })

        progress = await self.user_service.get_progress(user_id)

        context = {
            "user_id": str(user_id),
            "session_id": str(session_id),
            "history": history,
            "user_progress": progress,
            "tool_results": [],
        }

        self._session_cache[cache_key] = context
        return context

    async def update_context(
        self, user_id: uuid.UUID, session_id: uuid.UUID,
        message: str, context: dict
    ):
        cache_key = str(session_id)
        context["history"].append({"role": "user", "content": message})

        if "tool_results" in context:
            for tr in context.get("tool_results", []):
                if "result" in tr and "text" not in str(tr["result"]):
                    context["history"].append({
                        "role": "system",
                        "content": f"[工具 {tr['tool']} 结果]: {json.dumps(tr['result'], ensure_ascii=False)}",
                    })

        if len(context["history"]) > 40:
            context["history"] = context["history"][-40:]

        self._session_cache[cache_key] = context

    def clear_session(self, session_id: uuid.UUID):
        cache_key = str(session_id)
        self._session_cache.pop(cache_key, None)
