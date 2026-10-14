"""提醒 CRUD 路由。"""

from fastapi import APIRouter, Depends, HTTPException

from .. import db, reminder_store
from ..auth import require_token
from ..schemas import ReminderIn, ReminderUpdate

router = APIRouter(
    prefix="/api/reminders", tags=["reminders"], dependencies=[Depends(require_token)]
)


@router.get("")
def list_reminders():
    return db.list_reminders()


@router.get("/{reminder_id}/delivery")
def delivery_status(reminder_id: int) -> dict:
    """查询提醒的 WebSocket 发送尝试状态。"""
    delivery = reminder_store.delivery_status(reminder_id)
    if delivery is None:
        raise HTTPException(status_code=404, detail="提醒不存在")
    return delivery


@router.post("", status_code=201)
def create_reminder(payload: ReminderIn):
    return db.create_reminder(**payload.model_dump())


@router.put("/{reminder_id}")
def update_reminder(reminder_id: int, payload: ReminderUpdate):
    reminder = db.update_reminder(reminder_id, payload.model_dump(exclude_unset=True))
    if reminder is None:
        raise HTTPException(status_code=404, detail="提醒不存在")
    return reminder


@router.delete("/{reminder_id}", status_code=204)
def delete_reminder(reminder_id: int):
    if not db.delete_reminder(reminder_id):
        raise HTTPException(status_code=404, detail="提醒不存在")
