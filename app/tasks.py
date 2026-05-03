from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "teochew_learning",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
    task_soft_time_limit=540,
)


@celery_app.task(name="generate_learning_report")
def generate_learning_report(user_id: str, period: str = "weekly"):
    return {"status": "completed", "user_id": user_id, "period": period}


@celery_app.task(name="sync_knowledge_graph")
def sync_knowledge_graph():
    return {"status": "completed", "nodes_synced": 0}


@celery_app.task(name="cleanup_expired_sessions")
def cleanup_expired_sessions():
    return {"status": "completed", "sessions_cleaned": 0}
