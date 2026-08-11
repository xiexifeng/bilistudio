from fastapi import APIRouter, HTTPException, Query, Response
from utils.bili_api import (
    search_videos, get_video_detail, get_user_info, get_user_videos,
    get_followings, get_favorites, get_favorite_content, get_history,
    get_video_collection, get_playurl,
)
from schemas import BiliSearchResult, BiliVideoDetail, BiliUserInfo, BiliUserVideos
import requests
import time

router = APIRouter(prefix="/bilibili", tags=["Bilibili"])

# ====== 图片代理内存缓存 ======
_image_cache: dict[str, tuple[float, bytes, str]] = {}
_IMAGE_CACHE_TTL = 3600  # 1 小时
_MAX_IMAGE_CACHE = 200    # 最多缓存200张图


@router.get("/search", response_model=BiliSearchResult)
def search(keyword: str = Query(..., min_length=1), page: int = Query(1, ge=1)):
    """搜索B站视频（已过滤广告和推广内容）"""
    try:
        return search_videos(keyword, page)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/video/{bvid}", response_model=BiliVideoDetail)
def video_detail(bvid: str):
    """获取视频详情"""
    try:
        return get_video_detail(bvid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/video/{bvid}/collection")
def video_collection(bvid: str):
    """获取视频所属的合集及合集内所有视频（如视频不属于合集则返回 null）"""
    try:
        col = get_video_collection(bvid)
        if col is None:
            return {"collection": None}
        return {"collection": col.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/video/{bvid}/playurl")
def video_playurl(bvid: str, cid: int = Query(...), qn: int = Query(80, ge=16, le=127)):
    """获取视频播放直链地址（WBI 签名，流量走 B站 CDN，不经过本后端）"""
    try:
        return get_playurl(bvid, cid, qn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{mid}", response_model=BiliUserInfo)
def user_info(mid: int):
    """获取UP主信息"""
    try:
        return get_user_info(mid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{mid}/videos", response_model=BiliUserVideos)
def user_videos(mid: int, page: int = Query(1, ge=1)):
    """获取UP主视频列表（自动使用 WBI 签名，失败回退普通接口）"""
    try:
        return get_user_videos(mid, page)
    except RuntimeError as e:
        msg = str(e)
        if "-799" in msg or "过于频繁" in msg:
            raise HTTPException(status_code=429, detail=msg)
        raise HTTPException(status_code=500, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================== 以下接口需要B站登录态 =====================

@router.get("/followings")
def followings(page: int = Query(1, ge=1)):
    """获取当前B站账号的关注列表"""
    try:
        return get_followings(page)
    except Exception as e:
        raise HTTPException(status_code=401 if "登录" in str(e) else 500, detail=str(e))


@router.get("/favorites")
def favorites(page: int = Query(1, ge=1)):
    """获取当前B站账号的收藏夹列表"""
    try:
        return get_favorites(page)
    except Exception as e:
        raise HTTPException(status_code=401 if "登录" in str(e) else 500, detail=str(e))


@router.get("/favorites/{media_id}")
def favorite_content(media_id: int, page: int = Query(1, ge=1)):
    """获取某个收藏夹的视频内容"""
    try:
        return get_favorite_content(media_id, page)
    except Exception as e:
        raise HTTPException(status_code=401 if "登录" in str(e) else 500, detail=str(e))


@router.get("/history")
def history(page: int = Query(1, ge=1)):
    """获取当前B站账号的观看历史"""
    try:
        return get_history(page)
    except Exception as e:
        raise HTTPException(status_code=401 if "登录" in str(e) else 500, detail=str(e))


@router.get("/proxy/image")
def proxy_image(url: str = Query(...)):
    """代理B站图片，解决防盗链（带缓存）"""
    if url.startswith("//"):
        url = "https:" + url

    # 检查内存缓存
    now = time.time()
    if url in _image_cache:
        ts, content, ct = _image_cache[url]
        if now - ts < _IMAGE_CACHE_TTL:
            return Response(content=content, media_type=ct, headers={
                "Cache-Control": "public, max-age=3600",
            })

    try:
        resp = requests.get(
            url,
            headers={"Referer": "https://www.bilibili.com/"},
            timeout=15,
        )
        content_type = resp.headers.get("content-type", "image/jpeg")
        content = resp.content

        # 存入缓存（LRU 简单版：满了就清一半）
        if len(_image_cache) >= _MAX_IMAGE_CACHE:
            oldest = sorted(_image_cache.items(), key=lambda x: x[1][0])[:_MAX_IMAGE_CACHE // 2]
            for k, _ in oldest:
                del _image_cache[k]
        _image_cache[url] = (now, content, content_type)

        return Response(content=content, media_type=content_type, headers={
            "Cache-Control": "public, max-age=3600",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片代理失败: {e}")
