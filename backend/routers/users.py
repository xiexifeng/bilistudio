"""本地用户管理（无需注册，自动生成名字）"""
import random
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import User as UserModel
from schemas import UserOut, UserCreate, UserRename

router = APIRouter(prefix="/users", tags=["Users"])

# 随机名字池
_NAME_POOL = ["小明", "小方", "小华", "小美", "小丽", "小龙", "小虎", "小兔", "小星", "小月", "小云", "小风", "小宇", "小雪", "小乐", "小豆"]
_COLORS = ["#FF6B35", "#45B7D1", "#10B981", "#8B5CF6", "#F59E0B", "#EC4899", "#6366F1", "#14B8A6", "#F97316", "#84CC16"]


def _ensure_default_user(db: Session) -> UserModel:
    """确保存在默认用户"""
    user = db.query(UserModel).filter(UserModel.id == 1).first()
    if not user:
        name = random.choice(_NAME_POOL)
        color = random.choice(_COLORS)
        user = UserModel(id=1, name=name, color=color)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    """列出所有用户"""
    return db.query(UserModel).order_by(UserModel.id).all()


@router.post("", response_model=UserOut)
def create_user(data: UserCreate = None, db: Session = Depends(get_db)):
    """创建新用户（不传名字则自动生成）"""
    if data is None:
        data = UserCreate()
    # 从名字池中选一个未被占用的
    used_names = {r[0] for r in db.query(UserModel.name).all()}
    available = [n for n in _NAME_POOL if n not in used_names]
    name = data.name if data.name else (available[0] if available else f"用户{random.randint(1,99)}")
    color = random.choice(_COLORS)
    user = UserModel(name=name, color=color)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}/rename", response_model=UserOut)
def rename_user(user_id: int, data: UserRename, db: Session = Depends(get_db)):
    """重命名用户"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="用户不存在")
    user.name = data.name
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/active")
def mark_active(user_id: int, db: Session = Depends(get_db)):
    """标记用户活跃时间"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user:
        user.last_active_at = datetime.utcnow()
        db.commit()
    return {"ok": True}


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """删除用户及其所有数据"""
    if user_id == 1:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="不能删除默认用户")
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="用户不存在")
    # 删除该用户的收藏和进度
    from models import Collection, StageProgress
    db.query(Collection).filter(Collection.user_id == user_id).delete()
    db.query(StageProgress).filter(StageProgress.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return {"ok": True}
