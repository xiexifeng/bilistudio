"""学习路线/课程进度管理

学习路线定义在 ../frontend/src/curated.js 中（learningPaths），
后端只负责存储每个用户、每条路线、每个关卡的完成状态。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from database import get_db
from models import StageProgress as StageProgressModel
from schemas import StageProgressIn, StageProgressOut, CourseProgressOut

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/progress", response_model=list[CourseProgressOut])
def get_progress(
    user_id: int = Query(1),
    db: Session = Depends(get_db),
):
    """获取某用户所有路线的进度"""
    # 路线定义从 curated.js 来，这里只读数据库中的进度
    records = (
        db.query(StageProgressModel)
        .filter(StageProgressModel.user_id == user_id)
        .all()
    )
    # 按 path_id 分组
    groups: dict[str, list[StageProgressOut]] = {}
    for r in records:
        out = StageProgressOut.model_validate(r)
        groups.setdefault(r.path_id, []).append(out)

    result = []
    for pid, stages in groups.items():
        completed = sum(1 for s in stages if s.completed)
        result.append(CourseProgressOut(
            path_id=pid,
            stages=stages,
            completed_count=completed,
            total_count=len(stages),
        ))
    return result


@router.post("/progress", response_model=StageProgressOut)
def update_progress(
    data: StageProgressIn,
    user_id: int = Query(1),
    db: Session = Depends(get_db),
):
    """标记/取消标记一个关卡为已完成"""
    existing = (
        db.query(StageProgressModel)
        .filter(
            StageProgressModel.user_id == user_id,
            StageProgressModel.path_id == data.path_id,
            StageProgressModel.stage_id == data.stage_id,
        )
        .first()
    )
    if existing:
        existing.completed = data.completed
        existing.completed_at = datetime.utcnow() if data.completed else None
    else:
        existing = StageProgressModel(
            user_id=user_id,
            path_id=data.path_id,
            stage_id=data.stage_id,
            completed=data.completed,
            completed_at=datetime.utcnow() if data.completed else None,
        )
        db.add(existing)
    db.commit()
    db.refresh(existing)
    return StageProgressOut.model_validate(existing)
