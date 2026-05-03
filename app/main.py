from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.database import init_db
from app.utils.cache import cache
from app.middleware.security import RateLimitMiddleware, SecurityHeadersMiddleware, InputSanitizationMiddleware
from app.api.auth import router as auth_router, user_router
from app.api.learning import router as learning_router
from app.api.agent import router as agent_router
from app.api.analytics import router as analytics_router
from app.api.admin import router as admin_router
from app.api.websocket import manager, WebSocketHandler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await cache.connect()
    yield
    await cache.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="潮州方言伴学系统 - 集成AI的方言学习平台",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(InputSanitizationMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(learning_router)
app.include_router(agent_router)
app.include_router(analytics_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "admin": "/api/v1/admin/dashboard",
    }


@app.get("/health")
async def health_check():
    redis_status = "connected" if cache.redis_client else "disconnected"
    return {
        "status": "healthy",
        "redis": redis_status,
        "version": settings.APP_VERSION,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"} if not settings.DEBUG else {"detail": str(exc)},
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket):
    user_id = await WebSocketHandler.authenticate(websocket)
    if not user_id:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": data.get("timestamp")})

            elif msg_type == "subscribe":
                channel = data.get("channel")
                await websocket.send_json({
                    "type": "subscribed",
                    "channel": channel,
                    "timestamp": data.get("timestamp"),
                })

    except WebSocketDisconnect:
        manager.disconnect(user_id)
