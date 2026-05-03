import uuid
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserService
from app.services.learning_service import LearningService


class Toolbox:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)
        self.learning_service = LearningService(db)

    async def execute(self, tool_name: str, params: dict) -> dict[str, Any]:
        handlers = {
            "search_knowledge": self._search_knowledge,
            "get_lesson_content": self._get_lesson_content,
            "evaluate_pronunciation": self._evaluate_pronunciation,
            "get_user_progress": self._get_user_progress,
            "generate_exercise": self._generate_exercise,
            "get_review_queue": self._get_review_queue,
            "search_dialogue_scene": self._search_dialogue_scene,
            "log_learning_event": self._log_learning_event,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return {"error": f"未知工具: {tool_name}"}

        try:
            return await handler(params)
        except Exception as e:
            return {"error": str(e)}

    async def _search_knowledge(self, params: dict) -> dict:
        query = params.get("query", "")
        kp_type = params.get("kp_type")
        level = params.get("level")

        items, total = await self.learning_service.list_knowledge_points(
            kp_type=kp_type, level=level, search=query, page_size=10
        )

        return {
            "total": total,
            "items": [
                {
                    "id": str(item.id),
                    "title": item.title,
                    "kp_type": item.kp_type,
                    "level": item.level,
                    "pinyin": item.pinyin,
                    "hanzi": item.hanzi,
                }
                for item in items
            ],
        }

    async def _get_lesson_content(self, params: dict) -> dict:
        lesson_id = params.get("lesson_id")
        if not lesson_id:
            return {"error": "缺少lesson_id参数"}

        lesson = await self.learning_service.get_lesson(uuid.UUID(lesson_id))
        if not lesson:
            return {"error": "课程不存在"}

        return {
            "id": str(lesson.id),
            "title": lesson.title,
            "description": lesson.description,
            "level": lesson.level,
            "lesson_type": lesson.lesson_type,
            "kp_ids": [str(kp) for kp in (lesson.kp_ids or [])],
        }

    async def _evaluate_pronunciation(self, params: dict) -> dict:
        return {
            "overall_score": 78.5,
            "phoneme_accuracy": 82.0,
            "tone_accuracy": 72.0,
            "fluency": 80.0,
            "errors": [
                {"phoneme": "g", "expected": "浊音", "actual": "清音", "severity": "high"},
            ],
            "suggestion": "声母g的声带振动不足，建议先单独练习声带振动，再结合韵母。",
        }

    async def _get_user_progress(self, params: dict) -> dict:
        user_id_str = params.get("user_id", "")
        if not user_id_str:
            return {"error": "缺少user_id参数"}

        user_id = uuid.UUID(user_id_str)
        progress = await self.user_service.get_progress(user_id)
        return progress

    async def _generate_exercise(self, params: dict) -> dict:
        kp_id = params.get("kp_id")
        difficulty = params.get("difficulty", 1)
        count = params.get("count", 5)

        return {
            "kp_id": kp_id,
            "exercises": [
                {
                    "type": "choice",
                    "question": "以下哪个是潮州话'我'的正确发音？",
                    "options": ["ua²", "ua¹", "ua³", "ua⁴"],
                    "answer": 0,
                }
            ]
            * min(count, 5),
        }

    async def _get_review_queue(self, params: dict) -> dict:
        user_id_str = params.get("user_id", "")
        limit = params.get("limit", 10)

        if not user_id_str:
            return {"error": "缺少user_id参数"}

        user_id = uuid.UUID(user_id_str)
        items = await self.learning_service.get_review_queue(user_id, limit)

        return {
            "total": len(items),
            "items": [
                {
                    "kp_id": str(item.kp_id),
                    "title": item.kp_title,
                    "type": item.kp_type,
                    "p_learned": item.p_learned,
                    "days_overdue": item.days_overdue,
                }
                for item in items
            ],
        }

    async def _search_dialogue_scene(self, params: dict) -> dict:
        query = params.get("query", "")
        scenes, total = await self.learning_service.list_scenes(page_size=10)

        return {
            "total": total,
            "items": [
                {
                    "id": str(scene.id),
                    "title": scene.title,
                    "category": scene.scene_category,
                    "level": scene.level,
                    "mode": scene.mode,
                }
                for scene in scenes
            ],
        }

    async def _log_learning_event(self, params: dict) -> dict:
        return {"status": "logged", "event_id": str(uuid.uuid4())}
