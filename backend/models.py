from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger, Boolean, ForeignKey
from database import Base
from datetime import datetime


class User(Base):
    """本地用户（无需注册，自动生成）"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    color = Column(String(20), default="#FF6B35")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)


class Collection(Base):
    __tablename__ = "collection"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1, nullable=False, index=True)
    bvid = Column(String(20), index=True, nullable=False)
    title = Column(String(500), nullable=False)
    author = Column(String(200), nullable=False, index=True)
    author_mid = Column(BigInteger, nullable=True)
    pic = Column(String(500), nullable=True)
    duration = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    play_count = Column(BigInteger, nullable=True)
    pubdate = Column(String(20), nullable=True)
    note = Column(Text, nullable=True)
    status = Column(String(20), default="todo")  # todo | in_progress | done
    watch_progress = Column(Integer, default=0)  # 0-100 百分比
    created_at = Column(DateTime, default=datetime.utcnow)


class StageProgress(Base):
    """学习路线关卡进度（按用户）"""
    __tablename__ = "stage_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    path_id = Column(String(50), nullable=False)
    stage_id = Column(String(50), nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
