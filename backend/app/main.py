"""FastAPI 应用：组装路由，启动时初始化数据库。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import db
from .routers import courses, reminders, tasks


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="智能桌宠后端", version="0.1.0", lifespan=lifespan)

app.include_router(tasks.router)
app.include_router(courses.router)
app.include_router(reminders.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
