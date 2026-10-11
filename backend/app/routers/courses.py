"""课表 CRUD 路由。"""

from fastapi import APIRouter, Depends, HTTPException

from .. import db
from ..auth import require_token
from ..schemas import CourseIn, CourseUpdate

router = APIRouter(prefix="/api/courses", tags=["courses"], dependencies=[Depends(require_token)])


@router.get("")
def list_courses():
    return db.list_courses()


@router.post("", status_code=201)
def create_course(payload: CourseIn):
    return db.create_course(**payload.model_dump())


@router.put("/{course_id}")
def update_course(course_id: int, payload: CourseUpdate):
    course = db.update_course(course_id, payload.model_dump(exclude_unset=True))
    if course is None:
        raise HTTPException(status_code=404, detail="课表条目不存在")
    return course


@router.delete("/{course_id}", status_code=204)
def delete_course(course_id: int):
    if not db.delete_course(course_id):
        raise HTTPException(status_code=404, detail="课表条目不存在")
