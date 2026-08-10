"""统计数据聚合"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from database import get_db
from models import Collection as CollectionModel, User as UserModel
from schemas import StatsOverview

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("", response_model=StatsOverview)
def get_stats(
    user_id: int = Query(1),
    db: Session = Depends(get_db),
):
    """获取当前用户的统计面板数据"""
    base = db.query(CollectionModel).filter(CollectionModel.user_id == user_id)

    # 总数与状态分布
    total = base.count()
    todo_count = base.filter(CollectionModel.status == "todo").count()
    in_progress_count = base.filter(CollectionModel.status == "in_progress").count()
    done_count = base.filter(CollectionModel.status == "done").count()

    # 按作者分布
    author_rows = (
        db.query(CollectionModel.author, func.count(CollectionModel.id).label("cnt"))
        .filter(CollectionModel.user_id == user_id)
        .group_by(CollectionModel.author)
        .order_by(func.count(CollectionModel.id).desc())
        .limit(10)
        .all()
    )
    by_author = [{"author": r.author, "count": r.cnt} for r in author_rows]

    # 最近活跃天数（最近30天内有收藏的天数）
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_dates = (
        db.query(func.date(CollectionModel.created_at))
        .filter(
            CollectionModel.user_id == user_id,
            CollectionModel.created_at >= thirty_days_ago,
        )
        .distinct()
        .count()
    )
    recent_days = recent_dates

    # 总用户数
    total_users = db.query(UserModel).count()

    return StatsOverview(
        total_collection=total,
        todo_count=todo_count,
        in_progress_count=in_progress_count,
        done_count=done_count,
        by_author=by_author,
        recent_days=recent_days,
        total_users=total_users,
    )
