"""请求体模型（pydantic）。"""

from typing import Literal

from pydantic import BaseModel, Field


class CourseIn(BaseModel):
    name: str
    day_of_week: int = Field(ge=1, le=7)
    start_time: str
    end_time: str
    location: str = ""
    weeks: list[int] | None = None


class CourseUpdate(BaseModel):
    name: str | None = None
    day_of_week: int | None = Field(default=None, ge=1, le=7)
    start_time: str | None = None
    end_time: str | None = None
    location: str | None = None
    weeks: list[int] | None = None


class TaskIn(BaseModel):
    title: str
    note: str = ""
    due_at: str | None = None
    remind_at: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    note: str | None = None
    due_at: str | None = None
    remind_at: str | None = None
    done: bool | None = None


class ReminderIn(BaseModel):
    title: str
    body: str = ""
    remind_at: str
    channel: Literal["both", "pc", "phone"] = "both"
    task_id: int | None = None


class ReminderUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    remind_at: str | None = None
    channel: Literal["both", "pc", "phone"] | None = None
    done: bool | None = None
    task_id: int | None = None
