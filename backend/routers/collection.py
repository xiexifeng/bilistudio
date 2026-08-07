from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Collection as CollectionModel
from schemas import CollectionCreate, CollectionOut, CollectionList, ImportData
from utils.bili_api import get_video_detail

router = APIRouter(prefix="/collection", tags=["Collection"])

@router.post("", response_model=CollectionOut)
def add_collection(item: CollectionCreate, db: Session = Depends(get_db)):
    """添加收藏，支持自动补全B站信息"""
    # 如果只有 bvid，自动补全信息
    if not item.title or not item.author:
        try:
            detail = get_video_detail(item.bvid)
            item.title = item.title or detail.title
            item.author = item.author or detail.author
            item.author_mid = item.author_mid or detail.author_mid
            item.pic = item.pic or detail.pic
            item.duration = item.duration or detail.duration
            item.description = item.description or detail.description
            item.play_count = item.play_count or detail.play_count
            item.pubdate = item.pubdate or detail.pubdate
        except Exception:
            pass

    # 检查是否已存在
    existing = db.query(CollectionModel).filter(CollectionModel.bvid == item.bvid).first()
    if existing:
        # 更新
        for key, val in item.model_dump(exclude_unset=True).items():
            setattr(existing, key, val)
        db.commit()
        db.refresh(existing)
        return existing

    db_item = CollectionModel(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("", response_model=CollectionList)
def list_collection(
    author: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """查询收藏列表，支持按作者和关键词筛选"""
    query = db.query(CollectionModel)
    if author:
        query = query.filter(CollectionModel.author == author)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            (CollectionModel.title.ilike(like)) |
            (CollectionModel.author.ilike(like)) |
            (CollectionModel.note.ilike(like))
        )

    total = query.count()
    items = query.order_by(CollectionModel.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return CollectionList(items=items, total=total)

@router.delete("/{bvid}")
def delete_collection(bvid: str, db: Session = Depends(get_db)):
    """删除收藏"""
    item = db.query(CollectionModel).filter(CollectionModel.bvid == bvid).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return {"ok": True}

@router.get("/authors")
def get_authors(db: Session = Depends(get_db)):
    """获取所有UP主列表"""
    from sqlalchemy import func
    rows = db.query(
        CollectionModel.author,
        CollectionModel.author_mid,
        func.count(CollectionModel.id).label("count")
    ).group_by(CollectionModel.author, CollectionModel.author_mid).all()
    return [{"name": r.author, "mid": r.author_mid, "count": r.count} for r in rows]

@router.get("/export")
def export_collection(db: Session = Depends(get_db)):
    """导出全部收藏为JSON"""
    items = db.query(CollectionModel).all()
    return [CollectionOut.model_validate(i).model_dump() for i in items]

@router.post("/import")
def import_collection(data: ImportData, db: Session = Depends(get_db)):
    """批量导入收藏（按bvid去重）"""
    existing_bvids = {r[0] for r in db.query(CollectionModel.bvid).all()}
    imported = 0
    for item in data.data:
        if item.bvid in existing_bvids:
            continue
        db_item = CollectionModel(**item.model_dump())
        db.add(db_item)
        imported += 1
    db.commit()
    return {"imported": imported}

from fastapi import HTTPException
