from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ==================== B站数据模型 ====================
class BiliVideoItem(BaseModel):
    bvid: str
    title: str
    author: str
    author_mid: Optional[int] = None
    pic: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None
    play_count: Optional[int] = None
    pubdate: Optional[str] = None
    is_ad: bool = False

class BiliSearchResult(BaseModel):
    videos: List[BiliVideoItem]
    total: int
    page: int

class BiliUserInfo(BaseModel):
    mid: int
    name: str
    face: Optional[str] = None
    sign: Optional[str] = None
    follower: Optional[int] = None

class BiliUserVideos(BaseModel):
    videos: List[BiliVideoItem]
    total: int

class BiliVideoDetail(BaseModel):
    bvid: str
    title: str
    author: str
    author_mid: int
    pic: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[str] = None
    play_count: Optional[int] = None
    pubdate: Optional[str] = None
    cid: Optional[int] = None


class BiliCollectionItem(BaseModel):
    """合集中的单个视频"""
    bvid: str
    title: str
    pic: Optional[str] = None
    duration: Optional[str] = None
    play_count: Optional[int] = None
    pubdate: Optional[str] = None
    section_title: Optional[str] = None  # 所属分节名（如 正片/花絮）
    page: Optional[int] = None  # 分P视频的分页号（多P视频使用）

class BiliCollection(BaseModel):
    """视频所属合集（可能为空 None 表示不属于任何合集）"""
    season_id: int
    title: str
    cover: Optional[str] = None
    mid: int
    intro: Optional[str] = None
    total: int  # 合集总视频数
    videos: List[BiliCollectionItem]

# ==================== 收藏模型 ====================
class CollectionCreate(BaseModel):
    bvid: str
    title: str
    author: str
    author_mid: Optional[int] = None
    pic: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None
    play_count: Optional[int] = None
    pubdate: Optional[str] = None
    note: Optional[str] = None

class CollectionOut(CollectionCreate):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CollectionList(BaseModel):
    items: List[CollectionOut]
    total: int

# ==================== 认证模型 ====================
class LoginRequest(BaseModel):
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ImportData(BaseModel):
    data: List[CollectionCreate]
