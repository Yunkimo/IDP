"""FastAPI 应用：组装路由，启动时初始化数据库。"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import config, db
from .logging_config import install_log_filters
from .push_service import PushService
from .routers import courses, reminders, tasks, ws

install_log_filters()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """初始化数据库与广播服务，退出时释放连接。"""
    db.init_db()
    _app.state.push_service = PushService(
        config.WS_SEND_TIMEOUT_SECONDS, config.WS_CLOSE_TIMEOUT_SECONDS
    )
    try:
        yield
    finally:
        await _app.state.push_service.close_all()


app = FastAPI(title="智能桌宠后端", version="0.1.0", lifespan=lifespan)

app.include_router(tasks.router)
app.include_router(courses.router)
app.include_router(reminders.router)
app.include_router(ws.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
