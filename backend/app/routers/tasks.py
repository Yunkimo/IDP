"""日程/待办 CRUD 路由。"""

from fastapi import APIRouter, Depends, HTTPException

from .. import db
from ..auth import require_token
from ..schemas import TaskIn, TaskUpdate

router = APIRouter(prefix="/api/tasks", tags=["tasks"], dependencies=[Depends(require_token)])


@router.get("")
def list_tasks():
    return db.list_tasks()


@router.post("", status_code=201)
def create_task(payload: TaskIn):
    return db.create_task(**payload.model_dump())


@router.put("/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    task = db.update_task(task_id, payload.model_dump(exclude_unset=True))
    if task is None:
        raise HTTPException(status_code=404, detail="日程不存在")
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int):
    if not db.delete_task(task_id):
        raise HTTPException(status_code=404, detail="日程不存在")
