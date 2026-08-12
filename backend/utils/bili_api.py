try:
    import curl_cffi.requests as _http
    _USE_CURL_CFFI = True
except ImportError:
    import requests as _http
    _USE_CURL_CFFI = False

import re
import uuid
import time
import random
import hashlib
import hmac
import base64
import urllib.parse
import logging
import json
import math
import functools
import string as _string_module
from typing import List, Optional, Dict, Tuple
from schemas import BiliVideoItem, BiliSearchResult, BiliUserInfo, BiliUserVideos, BiliVideoDetail, BiliCollection, BiliCollectionItem
from utils import bili_auth
from config import settings

logger = logging.getLogger("bili")
logger.info(f"HTTP 后端: {'curl_cffi (模拟浏览器 TLS 指纹)' if _USE_CURL_CFFI else 'requests (纯 Python)'}")

# ====== 全局请求节流器 ======
_last_request_time = 0.0

# ====== 全局 -799 熔断器 ======
# 按接口路径熔断，避免影响 fallback 接口
# 任意 B站接口触发 -799 后，该路径冷却 60 秒
_path_cooldown: Dict[str, float] = {}  # path -> cooldown_until
_COOLDOWN_SECONDS = 60

def _get_path_key(url: str) -> str:
    """从 URL 提取接口路径作为熔断 key"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        # 取路径的前3段作为 key（如 /x/space/acc/info）
        parts = [p for p in parsed.path.split('/') if p]
        return '/' + '/'.join(parts[:3]) if len(parts) >= 3 else parsed.path
    except Exception:
        return url

def _throttle(url: str = ""):
    """确保两次 B站 API 请求之间有足够间隔（含随机抖动）。
    检查当前接口路径是否处于熔断冷却期。"""
    global _last_request_time
    # 检查当前路径的熔断状态
    if url:
        path_key = _get_path_key(url)
        cooldown_until = _path_cooldown.get(path_key, 0)
        remaining = cooldown_until - time.time()
        if remaining > 0:
            raise RuntimeError(f"B站接口熔断中 ({path_key})，请等待 {remaining:.0f} 秒后再试")
    now = time.time()
    elapsed = now - _last_request_time
    # 基础间隔 + 0~1.5s 随机抖动，避免固定间隔被识别为程序
    jitter = random.uniform(0, 1.5)
    interval = settings.bili_min_interval + jitter
    if elapsed < interval:
        wait = interval - elapsed
        time.sleep(wait)
    _last_request_time = time.time()


# User-Agent 轮换池 — 不要固定一个 UA，风控会把这个当成机器特征
_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

def _random_ua() -> str:
    return random.choice(_UA_POOL)


def _headers() -> dict:
    """每次请求都重新生成 headers，避免完全固定"""
    return {
        "User-Agent": _random_ua(),
        "Origin": "https://www.bilibili.com",
        "Referer": "https://www.bilibili.com/",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Sec-CH-UA": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "Connection": "keep-alive",
    }


_session_cache = None

# ====== TTL 内存缓存 ======
# 对 B站 API 读接口做短期缓存，减少重复请求触发风控
_cache: Dict[str, tuple[float, dict]] = {}

def _cache_key(url: str, params: dict = None) -> str:
    """生成缓存 key"""
    if params:
        # 排序保证一致性
        qs = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{url}?{qs}"
    return url

def _cached_request(url: str, params: dict = None, timeout: int = 15, ttl: int = 30, extra_headers: dict = None) -> dict:
    """
    带缓存的请求：同一 URL+params 在 TTL 秒内只请求一次。
    成功结果缓存 TTL 秒；-799 风控错误也缓存（cooldown），避免反复穿透加剧风控。
    extra_headers 用于按请求动态覆盖 headers（如空间页需要指定 Referer）。
    """
    key = _cache_key(url, params)
    now = time.time()
    if key in _cache:
        ts, data = _cache[key]
        if now - ts < ttl:
            # 检查是否是被缓存的 -799 冷却标记
            if isinstance(data, dict) and data.get("_cooldown"):
                raise RuntimeError(data["_error"])
            return data
        del _cache[key]
    try:
        result = _request(url, params, timeout, extra_headers=extra_headers)
        _cache[key] = (now, result)
        return result
    except RuntimeError as e:
        err_msg = str(e)
        # -799 风控错误也要缓存，冷却期内不再穿透到 B站
        if "-799" in err_msg:
            logger.warning(f"B站API ⚡ 命中 -799 冷却缓存 ({ttl}s): {key[:80]}")
            _cache[key] = (now, {"_cooldown": True, "_error": err_msg})
        raise

def clear_cache():
    """清除所有缓存（登录/退出后调用）"""
    _cache.clear()


def _gen_buvid3() -> str:
    """生成标准 buvid3 设备指纹（B站风控关键 cookie）
    格式: UUID + infoc 后缀，如: 365FC941-E43B-E635-D10B-14A06092BDCE13280infoc
    """
    return f"{uuid.uuid4()}infoc"


def _gen_buvid4() -> str:
    """生成 buvid4 设备指纹
    格式: UUID-时间戳-Base64，如: 9BE2CE9A-8F82-8278-C03A-A923D0902FDA18545-026011516-PaAP8UZVM/MV+25M0j4AEg%3D%3D
    """
    uid = str(uuid.uuid4()).upper()
    ts = str(int(time.time()))
    # 生成随机 Base64 部分（模拟浏览器指纹）
    fp_data = f"{uid}{ts}".encode()
    fp_b64 = base64.b64encode(fp_data).decode().rstrip('=')
    # 添加固定后缀模拟
    suffix = "PaAP8UZVM/MV+25M0j4AEg"
    return f"{uid}-{ts}-{suffix}"


def _gen_buvid_fp() -> str:
    """生成 buvid_fp 32位MD5指纹"""
    raw = f"{uuid.uuid4()}{int(time.time())}{random.random()}"
    return hashlib.md5(raw.encode()).hexdigest()


def _gen_b_nut() -> str:
    """生成 b_nut 时间戳 cookie"""
    return str(int(time.time() * 1000))


def _gen_b_lsid() -> str:
    """生成 b_lsid cookie"""
    return f"{uuid.uuid4().hex[:8]}_{int(time.time() * 1000)}"


def _gen_uuid() -> str:
    """生成 _uuid cookie，格式: UUID + infoc 后缀"""
    return f"{uuid.uuid4()}infoc"


def _ensure_visitor_cookies(s: _http.Session):
    """确保 session 有 B站 访客级 cookie，否则风控直接 -799
    优先使用 B站 首页返回的 cookie，仅在缺失时才生成补充
    """
    needed = {
        "buvid3": _gen_buvid3,
        "buvid4": _gen_buvid4,
        "buvid_fp": _gen_buvid_fp,
        "b_nut": _gen_b_nut,
        "b_lsid": _gen_b_lsid,
        "_uuid": _gen_uuid,
        # 额外的浏览器指纹 Cookie（降低风控概率）
        "browser_resolution": lambda: f"{random.choice(['1920', '1536', '1366'])}x{random.choice(['1080', '791', '768'])}",
        "CURRENT_FNVAL": lambda: "4048",
        "rpdid": lambda: f"|{uuid.uuid4().hex[:4]}|{uuid.uuid4().hex[:4]}|{uuid.uuid4().hex[:4]}'{uuid.uuid4().hex[:4]}~~",
        "theme-tip-show": lambda: "SHOWED",
        "theme-avatar-tip-show": lambda: "SHOWED",
        "home_feed_column": lambda: "5",
        "CURRENT_QUALITY": lambda: "0",
    }
    existing = s.cookies.get_dict()
    
    # 记录缺失的 cookie（需要生成补充）
    missing = []
    for key in needed:
        if key not in existing:
            val = needed[key]()
            s.cookies.set(key, val, domain=".bilibili.com")
            s.cookies.set(key, val, domain="api.bilibili.com")
            missing.append(key)
    
    if missing:
        logger.debug(f"补充缺失 cookie: {missing}")
    else:
        logger.debug("所有访客 cookie 完整，无需补充")


# ====== B站 GenWebTicket 鉴权 ======
# bili_ticket 是B站新的鉴权机制，用于降低风控概率
_bili_ticket: Optional[str] = None
_bili_ticket_expires: float = 0.0


def _hmac_sha256(key: str, message: str) -> str:
    """使用 HMAC-SHA256 计算签名"""
    h = hmac.new(key.encode(), message.encode(), hashlib.sha256)
    return h.hexdigest()


def _get_bili_ticket(s: _http.Session) -> bool:
    """获取 bili_ticket（B站新鉴权）
    返回: 是否获取成功
    """
    global _bili_ticket, _bili_ticket_expires, _wbi_keys, _wbi_keys_ts
    
    # 检查缓存的 ticket 是否仍然有效
    now = time.time()
    if _bili_ticket and now < _bili_ticket_expires:
        logger.debug(f"bili_ticket 缓存有效，过期时间: {_bili_ticket_expires - now:.0f}s")
        s.cookies.set("bili_ticket", _bili_ticket, domain=".bilibili.com")
        s.cookies.set("bili_ticket", _bili_ticket, domain="api.bilibili.com")
        s.cookies.set("bili_ticket_expires", str(int(_bili_ticket_expires)), domain=".bilibili.com")
        return True
    
    # 获取新 ticket
    try:
        timestamp = int(time.time())
        hexsign = _hmac_sha256("XgwSnGZ1p", f"ts{timestamp}")
        
        # 获取 bili_jct 作为 csrf 参数（已登录时需要）
        # curl_cffi 的 cookies 迭代返回字符串名称，需要用 get_dict() 获取
        csrf = ""
        cookies_dict = s.cookies.get_dict()
        if "bili_jct" in cookies_dict:
            csrf = cookies_dict["bili_jct"]
        
        url = "https://api.bilibili.com/bapis/bilibili.api.ticket.v1.Ticket/GenWebTicket"
        params = {
            "key_id": "ec02",
            "hexsign": hexsign,
            "context[ts]": str(timestamp),
            "csrf": csrf,  # 已登录时使用 bili_jct
        }
        
        resp = s.post(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get("code") == 0:
            ticket_data = data["data"]
            _bili_ticket = ticket_data["ticket"]
            ttl = ticket_data.get("ttl", 259200)  # 默认3天
            _bili_ticket_expires = now + ttl - 3600  # 提前1小时刷新
            
            # 获取 WBI 密钥（GenWebTicket 返回的 nav 数据）
            nav_data = ticket_data.get("nav", {})
            if nav_data:
                # GenWebTicket 格式: nav.img / nav.sub (完整 URL)
                img_url = nav_data.get("img", "")
                sub_url = nav_data.get("sub", "")
                if img_url and sub_url:
                    # 从 URL 中提取 key（格式: https://xxx/xxx/{key}.png）
                    img_key = img_url.rsplit("/", 1)[-1].split(".")[0] if "/" in img_url else img_url
                    sub_key = sub_url.rsplit("/", 1)[-1].split(".")[0] if "/" in sub_url else sub_url
                    _wbi_keys = (img_key, sub_key)
                    _wbi_keys_ts = now
                    logger.info(f"WBI 密钥已从 GenWebTicket 更新")
            
            # 设置 cookie
            s.cookies.set("bili_ticket", _bili_ticket, domain=".bilibili.com")
            s.cookies.set("bili_ticket", _bili_ticket, domain="api.bilibili.com")
            s.cookies.set("bili_ticket_expires", str(int(_bili_ticket_expires)), domain=".bilibili.com")
            
            logger.info(f"bili_ticket 获取成功，有效期: {ttl}s")
            return True
        else:
            logger.warning(f"GenWebTicket 返回错误: {data.get('code')} - {data.get('message')}")
            return False
    except Exception as e:
        logger.warning(f"获取 bili_ticket 失败: {e}")
        return False


def refresh_bili_ticket() -> bool:
    """强制刷新 bili_ticket"""
    global _bili_ticket, _bili_ticket_expires
    _bili_ticket = None
    _bili_ticket_expires = 0.0
    s = _create_session()
    return _get_bili_ticket(s)


# 记录 session 缓存创建时的登录态，用于自动检测登录态变化
_session_logged_in: bool = False


def _create_session() -> _http.Session:
    """创建带B站有效cookie的session（先访问主页预热获取完整访客cookie）"""
    global _session_cache, _session_logged_in

    # 检测登录态是否变化：如果登录态变了，废弃旧缓存重新创建
    is_now_logged_in = bili_auth.is_logged_in()
    if _session_cache is not None and _session_logged_in == is_now_logged_in:
        return _session_cache

    if _session_cache is not None:
        logger.info(f"B站 登录态变化（{'已登录' if is_now_logged_in else '未登录'}），重建 session")

    # curl_cffi 支持 impersonate 模拟浏览器 TLS 指纹（JA3），绕过风控
    if _USE_CURL_CFFI:
        s = _http.Session(impersonate="chrome120")
        # 只添加必要的请求头，不覆盖 curl_cffi 的浏览器指纹
        s.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
    else:
        s = _http.Session()
        s.headers.update(_headers())

    # 关键：先访问B站首页获取基础访客cookie（buvid3, b_nut等）
    # 只访问 search.bilibili.com 拿不到这些关键cookie
    _throttle("https://www.bilibili.com/")  # 节流！预热请求也必须遵守间隔
    try:
        resp = s.get("https://www.bilibili.com/", timeout=10)
        logger.debug(f"B站首页访问: status={resp.status_code}, cookies={list(s.cookies.get_dict().keys())}")
    except Exception as e:
        logger.warning(f"B站首页访问失败: {e}")

    # 先注入B站登录cookie（如果已登录）
    # 必须在获取 bili_ticket 之前注入，因为 GenWebTicket 需要 bili_jct 作为 csrf
    # 必须在 _ensure_visitor_cookies 之前注入，因为登录 Cookie 中包含真实的设备指纹
    logged_cookies = []
    if is_now_logged_in:
        for k, v in bili_auth.get_cookies().items():
            s.cookies.set(k, v, domain=".bilibili.com")
            s.cookies.set(k, v, domain="api.bilibili.com")
            if k in ("SESSDATA", "bili_jct", "DedeUserID", "sid"):
                logged_cookies.append(k)

    # 最后确保关键cookie存在（如果登录Cookie中有，就使用登录Cookie中的值；缺失的才生成）
    _ensure_visitor_cookies(s)

    # 获取 bili_ticket（B站新鉴权机制）- 需要登录 cookie 中的 bili_jct
    _get_bili_ticket(s)

    _session_cache = s
    _session_logged_in = is_now_logged_in
    
    # 打印当前 cookie 状态
    cookies_dict = s.cookies.get_dict()
    has_ticket = "bili_ticket" in cookies_dict
    logger.info(f"B站 session 创建完成 | 登录态={'已登录' if is_now_logged_in else '未登录'} | bili_ticket={'✅' if has_ticket else '❌'} | 登录Cookie: {logged_cookies}")
    return s


def reset_session_cache():
    """登录/退出后重置session缓存和API缓存"""
    global _session_cache, _session_logged_in
    _session_cache = None
    _session_logged_in = False
    clear_cache()
    logger.info("B站 session 缓存已重置（登录/退出触发）")


# 广告/推广关键词黑名单
_AD_KEYWORDS = ["广告", "推广", "赞助", "恰饭", "测评请私信", "合作请私信", "商务合作"]


def _is_ad(video: dict) -> bool:
    title = video.get("title", "")
    desc = video.get("description", "") or video.get("desc", "")
    for kw in _AD_KEYWORDS:
        if kw in title or kw in desc:
            return True
    emoji_count = len(re.findall(
        r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF'
        r'\U00002702-\U000027B0\U000024C2-\U0001F251]', title
    ))
    if emoji_count >= 3 and len(title) < 20:
        return True
    return False


def _clean_title(title: str) -> str:
    if not title:
        return ""
    title = re.sub(r'<[^>]+>', '', title)
    return title.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').strip()


def _format_duration(dur) -> str:
    if not dur:
        return ""
    if isinstance(dur, str):
        if ":" in dur:
            return dur.split(":")[-2] + ":" + dur.split(":")[-1] if len(dur.split(":")) == 3 else dur
        try:
            dur = int(dur)
        except (ValueError, TypeError):
            return dur
    m, s = divmod(int(dur), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m}:{s:02d}"


def _format_pubdate(ts) -> str:
    if not ts:
        return ""
    try:
        return __import__("datetime").datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return str(ts)


def _request(url: str, params: dict = None, timeout: int = 15, retries: int = None, extra_headers: dict = None) -> dict:
    """
    统一请求：带session、cookie和错误处理。
    遇到 -799（请求过于频繁）立即触发该接口路径的熔断，允许 fallback 到其他接口。
    仅对网络错误进行重试，对风控错误直接返回。
    extra_headers 会合并到请求中，覆盖 session 默认 headers（如动态 Referer）。
    """
    if retries is None:
        retries = settings.bili_retry_count
    _throttle(url)  # 按路径节流检查
    s = _create_session()

    last_error = None
    for attempt in range(retries):
        t0 = time.time()
        try:
            resp = s.get(url, params=params, timeout=timeout, headers=extra_headers)
            elapsed = (time.time() - t0) * 1000
            resp.raise_for_status()
            data = resp.json()
            code = data.get("code", 0)
            if code == 0:
                logger.info(f"B站API ✓ {url.rsplit('/',2)[-2]}/{url.rsplit('/',1)[-1]}  params={params}  ({elapsed:.0f}ms)")
                return data
            if code == -799:
                # 风控错误：触发该接口路径熔断，不重试，但允许 fallback 到其他接口
                path_key = _get_path_key(url)
                _path_cooldown[path_key] = time.time() + _COOLDOWN_SECONDS
                detail = json.dumps(data, ensure_ascii=False, indent=2)[:500]
                logger.warning(f"B站API ⚠ -799 风控 ({elapsed:.0f}ms) | {path_key}\n  → 该路径触发 {_COOLDOWN_SECONDS}s 熔断（其他接口仍可用）\n  → 响应详情: {detail}")
                raise RuntimeError(f"B站API错误 (-799): {path_key} 请求过于频繁")
            if code == -403:
                # 权限错误：直接返回，不重试
                detail = json.dumps(data, ensure_ascii=False, indent=2)[:500]
                logger.warning(f"B站API ⚠ -403 权限不足 ({elapsed:.0f}ms) | {url.rsplit('/',2)[-2]}/{url.rsplit('/',1)[-1]}\n  → 响应详情: {detail}")
                raise RuntimeError(f"B站API错误 (-403): 访问权限不足")
            detail = json.dumps(data, ensure_ascii=False, indent=2)[:500]
            logger.error(f"B站API ✗ code={code} msg={data.get('message','unknown')} ({elapsed:.0f}ms) | {url.rsplit('/',2)[-2]}/{url.rsplit('/',1)[-1]}  params={params}\n  → 响应详情: {detail}")
            raise RuntimeError(f"B站API错误 ({code}): {data.get('message', 'unknown')}")
        except RuntimeError:
            # 业务错误（-799, -403 等）直接抛出，不重试
            raise
        except Exception as e:
            # 网络错误才重试
            elapsed = (time.time() - t0) * 1000
            resp_detail = ""
            try:
                if hasattr(e, 'response') and e.response is not None:
                    resp_detail = f" | status={e.response.status_code}"
            except Exception:
                pass
            if attempt < retries - 1:
                delay = (2 ** (attempt + 1)) + random.uniform(0, 1)
                logger.warning(f"B站API ⚠ 网络错误: {e}{resp_detail} ({elapsed:.0f}ms) | {delay:.1f}s 后重试")
                time.sleep(delay)
                last_error = e
                continue
            logger.error(f"B站API ✗ 网络错误（已重试{retries}次）: {e}{resp_detail} ({elapsed:.0f}ms) | {url.rsplit('/',2)[-2]}/{url.rsplit('/',1)[-1]}")
            raise RuntimeError(f"B站API请求失败（已重试{retries}次）: {e}")


# ====== WBI 签名（Wbi Arc Search 备选接口） ======

# B站 WBI 混肴密钥映射表
_MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]

# WBI 密钥缓存
_wbi_keys: Optional[Tuple[str, str]] = None
_wbi_keys_ts: float = 0.0
_WBI_KEYS_TTL = 3600  # 1 小时


def _get_mixin_key(raw: str) -> str:
    """从原始密钥推导 mixin key"""
    return "".join(raw[i] for i in _MIXIN_KEY_ENC_TAB if i < len(raw))[:32]


def _fetch_wbi_keys() -> Tuple[str, str]:
    """获取 WBI 签名所需的 img_key 和 sub_key"""
    global _wbi_keys, _wbi_keys_ts
    now = time.time()
    if _wbi_keys and (now - _wbi_keys_ts) < _WBI_KEYS_TTL:
        return _wbi_keys

    s = _create_session()
    _throttle("https://api.bilibili.com/x/web-interface/nav")  # 节流！nav 请求也必须遵守间隔
    resp = s.get("https://api.bilibili.com/x/web-interface/nav", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    wbi_img = data["data"]["wbi_img"]
    # img_url 和 sub_url 的格式: https://xxx/xxx/xxx.png
    # 从文件名提取 key（去掉扩展名后的部分）
    img_key = wbi_img["img_url"].rsplit("/", 1)[-1].split(".")[0]
    sub_key = wbi_img["sub_url"].rsplit("/", 1)[-1].split(".")[0]

    _wbi_keys = (img_key, sub_key)
    _wbi_keys_ts = now
    return _wbi_keys


def _sign_wbi(params: Dict) -> Dict:
    """对参数做 WBI 签名，返回加了 wts 和 w_rid 的新字典
    注意：wts 参与 w_rid 的计算
    """
    img_key, sub_key = _fetch_wbi_keys()
    mixin_key = _get_mixin_key(img_key + sub_key)

    # 过滤特殊字符（B站规范）
    def _filter(s):
        return "".join(ch for ch in str(s) if ch not in "!'()*")

    # 加时间戳（wts 参与签名）
    signed = dict(params)
    signed["wts"] = int(time.time())

    # 排序
    sorted_params = sorted(signed.items(), key=lambda x: x[0])
    # 拼接 query string
    query = urllib.parse.urlencode({k: _filter(v) for k, v in sorted_params})
    # MD5 签名
    w_rid = hashlib.md5((query + mixin_key).encode("utf-8")).hexdigest()
    
    signed["w_rid"] = w_rid
    return signed


# ====== dm_* 浏览器指纹参数 ======
# 参考 yt-dlp 项目实现：https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/bilibili.py
# 这些参数用于 B 站的浏览器指纹检测，必须正确生成

@functools.lru_cache(maxsize=None)
def _screen_dimensions():
    """随机选择一个常见屏幕尺寸"""
    dims, prefs = zip(
        ((1920, 1080), 18),
        ((1366, 768), 18),
        ((1536, 864), 17),
        ((1280, 720), 8),
        ((2560, 1440), 7),
        ((1440, 900), 5),
        ((1600, 900), 5),
    )
    return random.choices(dims, weights=prefs)[0]

def _get_wh(width=1920, height=1080):
    """计算 dm_img_inter 中的 wh 值"""
    rnd = math.floor(114 * random.random())
    return [2 * width + 2 * height + 3 * rnd, 4 * width - height + rnd, rnd]

def _get_of(scroll_top=10, scroll_left=10):
    """计算 dm_img_inter 中的 of 值"""
    rnd = math.floor(514 * random.random())
    return [3 * scroll_top + 2 * scroll_left + rnd, 4 * scroll_top - 4 * scroll_left + 2 * rnd, rnd]

def _gen_dm_params() -> dict:
    """生成完整的 dm_* 参数，对标真实浏览器请求"""
    width, height = _screen_dimensions()
    
    # dm_img_str: 随机 base64 字符串
    dm_img_str_raw = ''.join(random.choices(_string_module.printable, k=random.randint(16, 64)))
    dm_img_str = base64.b64encode(dm_img_str_raw.encode()).decode()[:-2]
    
    # dm_cover_img_str: 随机 base64 字符串
    dm_cover_img_str_raw = ''.join(random.choices(_string_module.printable, k=random.randint(32, 128)))
    dm_cover_img_str = base64.b64encode(dm_cover_img_str_raw.encode()).decode()[:-2]
    
    # dm_img_inter: 紧凑 JSON 格式
    dm_img_inter = json.dumps({
        "ds": [],
        "wh": _get_wh(width, height),
        "of": _get_of(random.randint(0, 100), 0),
    }, separators=(',', ':'))
    
    return {
        "dm_img_list": "[]",
        "dm_img_str": dm_img_str,
        "dm_cover_img_str": dm_cover_img_str,
        "dm_img_inter": dm_img_inter,
    }

def _sign_with_dm(base_params: dict) -> dict:
    """对参数进行 WBI 签名，并自动添加 dm_* 浏览器指纹参数"""
    params = {**base_params, **_gen_dm_params()}
    return _sign_wbi(params)


# ====== UP主视频列表 - WBI 签名版（对标真实浏览器请求） ======

def _get_user_videos_wbi(mid: int, page: int = 1, ps: int = 30) -> BiliUserVideos:
    """使用 WBI 签名接口获取 UP 主视频列表，参数对标真实浏览器请求"""
    params = _sign_with_dm({
        "mid": mid, "ps": ps, "pn": page,
        "tid": 0, "keyword": "", "order": "pubdate",
        "index": 0,
        "special_type": "",
        "order_avoided": "true",
        "platform": "web",
        "web_location": "333.1387",
    })
    data = _cached_request(
        "https://api.bilibili.com/x/space/wbi/arc/search",
        params, ttl=settings.bili_video_list_cache_ttl,
        extra_headers={"Referer": f"https://space.bilibili.com/{mid}/video"},
    )
    vlist = data["data"].get("list", {}).get("vlist", [])
    videos: List[BiliVideoItem] = []
    for item in vlist:
        videos.append(BiliVideoItem(
            bvid=item.get("bvid", ""), title=_clean_title(item.get("title", "")),
            author=item.get("author", ""), author_mid=mid,
            pic=item.get("pic", ""), duration=_format_duration(item.get("length")),
            description=item.get("description", ""), play_count=item.get("play"),
            pubdate=_format_pubdate(item.get("created", 0)),
        ))
    return BiliUserVideos(videos=videos, total=data["data"].get("page", {}).get("count", 0))


# ===================== 搜索 =====================

def _search_lightweight(keyword: str, page: int) -> dict:
    """轻量搜索请求：不走带登录 cookie 的 session，避免 412 风控。
    匿名请求 legacy 接口，B站不触发登录态异常检测。
    412 偶发时自动重试 2 次。"""
    url = "https://api.bilibili.com/x/web-interface/search/type"
    params = {"search_type": "video", "keyword": keyword, "page": page, "pagesize": 20}
    headers = {
        "User-Agent": _random_ua(),
        "Referer": "https://www.bilibili.com/",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    last_err = None
    for attempt in range(3):
        if _USE_CURL_CFFI:
            s = _http.Session(impersonate="chrome120")
        else:
            s = _http.Session()
        s.headers.update(headers)
        try:
            resp = s.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") == 0:
                logger.info(f"B站API ✓ search/light  keyword={keyword} page={page} ({attempt+1}次尝试)")
                return data
            logger.warning(f"B站API ⚠ search/light code={data.get('code')} msg={data.get('message')}")
            return data
        except Exception as e:
            last_err = e
            status = getattr(getattr(e, 'response', None), 'status_code', '?')
            logger.warning(f"B站API ⚠ search/light {status} attempt={attempt+1} ({e})")
            if attempt < 2:
                time.sleep(0.5 + attempt * 0.5)
    raise RuntimeError(f"搜索请求失败: {last_err}")


def search_videos(keyword: str, page: int = 1) -> BiliSearchResult:
    """搜索视频（匿名轻量请求 legacy 接口，无 WBI 签名、无 v_voucher 风控、缓存可命中）"""
    # 缓存检查
    cache_key = _cache_key(
        "https://api.bilibili.com/x/web-interface/search/type",
        {"search_type": "video", "keyword": keyword, "page": page, "pagesize": 20},
    )
    now = time.time()
    if cache_key in _cache:
        ts, data = _cache[cache_key]
        if now - ts < settings.bili_search_cache_ttl:
            if not (isinstance(data, dict) and data.get("_cooldown")):
                result = data.get("data", {})
                videos_raw = result.get("result", [])
                return _build_search_result(videos_raw, result, page)

    # 轻量请求（不走登录 session）
    _throttle("https://api.bilibili.com/x/web-interface/search/type")
    try:
        data = _search_lightweight(keyword, page)
        _cache[cache_key] = (now, data)
        result = data.get("data", {})
        videos_raw = result.get("result", [])
        return _build_search_result(videos_raw, result, page)
    except RuntimeError:
        # 轻量请求全部失败，回退到带 session 的 legacy 请求
        logger.warning("搜索轻量请求失败，回退 session 请求")
        data = _cached_request(
            "https://api.bilibili.com/x/web-interface/search/type",
            {"search_type": "video", "keyword": keyword, "page": page, "pagesize": 20},
            ttl=settings.bili_search_cache_ttl,
        )
        result = data.get("data", {})
        videos_raw = result.get("result", [])
        return _build_search_result(videos_raw, result, page)


def _build_search_result(videos_raw: list, result: dict, page: int) -> "BiliSearchResult":
    """从搜索结果原始数据构建 BiliSearchResult"""
    videos: List[BiliVideoItem] = []
    for item in videos_raw:
        if _is_ad(item):
            continue
        videos.append(BiliVideoItem(
            bvid=item.get("bvid", ""), title=_clean_title(item.get("title", "")),
            author=item.get("author", ""), author_mid=item.get("mid"),
            pic=item.get("pic", ""), duration=_format_duration(item.get("duration")),
            description=item.get("description", ""), play_count=item.get("play"),
            pubdate=_format_pubdate(item.get("pubdate", 0)),
        ))
    return BiliSearchResult(videos=videos, total=result.get("numResults", 0), page=page)


# ===================== 视频详情 =====================

def _build_collection_from_view(info: dict, bvid: str) -> Optional[BiliCollection]:
    """从 B站 view 接口的 data 字段中提取合集/多P信息。"""
    # 1. 优先检查 UGC 合集 (ugc_season)
    ugc = info.get("ugc_season")
    if ugc:
        season_id = ugc.get("id")
        if season_id:
            videos: List[BiliCollectionItem] = []
            sections = ugc.get("sections", []) or []
            top_episodes = ugc.get("episodes", []) or []
            for section in sections:
                section_title = section.get("title", "")
                for ep in section.get("episodes", []) or []:
                    item = _parse_collection_episode(ep, section_title)
                    if item:
                        videos.append(item)
            if not videos:
                for ep in top_episodes:
                    item = _parse_collection_episode(ep, None)
                    if item:
                        videos.append(item)
            if videos:
                total = ugc.get("ep_count") or ugc.get("stat", {}).get("total") or len(videos)
                return BiliCollection(
                    season_id=season_id,
                    title=ugc.get("title", ""),
                    cover=ugc.get("cover"),
                    mid=ugc.get("mid", info.get("owner", {}).get("mid", 0)),
                    intro=ugc.get("intro") or None,
                    total=total,
                    videos=videos,
                )

    # 2. 其次检查多P视频 (pages)
    pages = info.get("pages", [])
    if len(pages) > 1:
        videos: List[BiliCollectionItem] = []
        video_pic = info.get("pic")
        for p in pages:
            videos.append(BiliCollectionItem(
                bvid=bvid,
                title=_clean_title(p.get("part", "")),
                pic=video_pic,
                duration=_format_duration(p.get("duration", 0)),
                page=p.get("page", 1),
                cid=p.get("cid"),
            ))
        return BiliCollection(
            season_id=0,
            title=info.get("title", "") or "视频选集",
            cover=video_pic,
            mid=info.get("owner", {}).get("mid", 0),
            total=len(pages),
            videos=videos,
        )

    return None


def get_video_detail(bvid: str) -> BiliVideoDetail:
    """获取视频详情（WBI 签名 + 浏览器指纹），同时附带合集/多P信息。

    一次 B站 view 接口请求同时返回视频详情 + collection，避免前端再发一次 collection 请求。
    """
    params = _sign_with_dm({
        "bvid": bvid,
        "web_location": "333.1387",
    })
    try:
        data = _cached_request(
            "https://api.bilibili.com/x/web-interface/wbi/view",
            params, ttl=60,
        )
    except RuntimeError:
        logger.warning("WBI video_detail 失败，回退 legacy")
        data = _cached_request(
            "https://api.bilibili.com/x/web-interface/view",
            {"bvid": bvid}, ttl=60,
        )
    info = data["data"]
    owner = info.get("owner", {})
    collection = _build_collection_from_view(info, bvid)
    return BiliVideoDetail(
        bvid=info.get("bvid", ""), title=_clean_title(info.get("title", "")),
        author=owner.get("name", ""), author_mid=owner.get("mid"),
        pic=info.get("pic", ""), description=info.get("desc", ""),
        duration=_format_duration(info.get("duration", 0)),
        play_count=info.get("stat", {}).get("view"),
        pubdate=_format_pubdate(info.get("pubdate", 0)), cid=info.get("cid"),
        collection=collection,
    )


# ===================== 视频合集 =====================

def _fetch_video_view_raw(bvid: str) -> dict:
    """直接调 WBI view 接口拿原始响应（用于提取 ugc_season 合集信息）"""
    params = _sign_with_dm({"bvid": bvid, "web_location": "333.1387"})
    return _cached_request(
        "https://api.bilibili.com/x/web-interface/wbi/view",
        params, ttl=60,
    )


def get_video_collection(bvid: str) -> Optional[BiliCollection]:
    """从视频详情接口提取视频所属的合集及所有视频列表。

    已被 get_video_detail 内联复用；本接口保留供独立调用场景使用。
    """
    try:
        data = _fetch_video_view_raw(bvid)
    except RuntimeError as e:
        logger.warning(f"get_video_collection: view 接口失败 ({e})")
        return None
    return _build_collection_from_view(data.get("data", {}), bvid)


def _parse_collection_episode(ep: dict, section_title: Optional[str]) -> Optional[BiliCollectionItem]:
    """把 ugc_season episode 转成 BiliCollectionItem"""
    bvid = ep.get("bvid", "")
    if not bvid:
        return None
    arc = ep.get("arc", {}) or {}
    return BiliCollectionItem(
        bvid=bvid,
        title=_clean_title(ep.get("title") or arc.get("title", "")),
        pic=arc.get("pic"),
        duration=_format_duration(arc.get("duration", 0)),
        play_count=arc.get("stat", {}).get("view"),
        pubdate=_format_pubdate(arc.get("pubdate", 0)),
        section_title=section_title,
    )


# ===================== UP主信息 & 视频 =====================

def get_user_info(mid: int) -> BiliUserInfo:
    """获取 UP 主基本信息
    优先使用 card 接口（风控最低），失败回退 WBI，最后 legacy
    """
    # 方案 1: card 接口（最稳定，风控最低）
    try:
        return _get_user_info_card(mid)
    except RuntimeError as e:
        logger.info(f"user_info card 接口不可用 ({e})，尝试 WBI")
    
    # 方案 2: WBI 接口
    try:
        return _get_user_info_wbi(mid)
    except RuntimeError as e:
        logger.info(f"user_info WBI 不可用 ({e})，尝试 legacy")
    
    # 方案 3: legacy 接口
    return _get_user_info_legacy(mid)


def _get_user_info_card(mid: int) -> BiliUserInfo:
    """用户名片接口 x/web-interface/card（风控最低，参数简单）"""
    data = _cached_request(
        "https://api.bilibili.com/x/web-interface/card",
        {"mid": mid, "photo": "false"}, ttl=120,
        extra_headers={"Referer": f"https://space.bilibili.com/{mid}"},
    )
    card = data["data"]["card"]
    return BiliUserInfo(
        mid=card.get("mid", mid),
        name=card.get("name", ""),
        face=card.get("face", ""),
        sign=card.get("sign", ""),
        follower=card.get("fans", 0),
    )


def _get_user_info_wbi(mid: int) -> BiliUserInfo:
    """WBI 签名版，参数对标真实浏览器请求（空间页）"""
    params = _sign_with_dm({
        "mid": mid,
        "web_location": "1550101",  # 空间页专用，不是搜索页的 333.1387
    })
    data = _cached_request(
        "https://api.bilibili.com/x/space/wbi/acc/info", params, ttl=120,
        extra_headers={"Referer": f"https://space.bilibili.com/{mid}"},
    )
    info = data["data"]
    return _build_user_info(info, mid)


def _get_user_info_legacy(mid: int) -> BiliUserInfo:
    """legacy 接口（无 WBI 签名，兜底）"""
    data = _cached_request(
        "https://api.bilibili.com/x/space/acc/info", {"mid": mid}, ttl=120,
        extra_headers={"Referer": f"https://space.bilibili.com/{mid}"},
    )
    info = data["data"]
    return _build_user_info(info, mid)


def _build_user_info(info: dict, mid: int) -> BiliUserInfo:
    return BiliUserInfo(mid=info.get("mid", mid), name=info.get("name", ""),
                        face=info.get("face", ""), sign=info.get("sign", ""),
                        follower=info.get("follower", 0))


def get_user_videos(mid: int, page: int = 1, ps: int = 30) -> BiliUserVideos:
    """获取 UP 主视频列表
    使用多级 fallback：WBI → legacy。两次都失败直接报错，不拿错误数据糊弄。

    注意：早期实现里有第三级 fallback `x/polymer/web-dynamic/v1/feed/space`（动态流接口），
    但它返回的是 "用户动态" 而非 "用户发布的视频"，会混入转发的/点赞的别人的视频，
    archive 字段也缺少 author 信息，且部分 bvid 实际无法访问（-404/62002），
    导致用户看到"UP 主名字是他的，点进去却不是他的视频"。已彻底移除。
    """
    errors = []

    # 方案 1: WBI 接口
    try:
        return _get_user_videos_wbi(mid, page, ps)
    except RuntimeError as e:
        errors.append(f"WBI: {e}")
        logger.info(f"user_videos WBI 不可用，尝试 legacy")

    # 方案 2: legacy 接口
    try:
        return _get_user_videos_legacy(mid, page, ps)
    except RuntimeError as e:
        errors.append(f"legacy: {e}")
        logger.error(f"user_videos 接口均不可用: {'; '.join(errors)}")
        # 直接抛错，不拿错误数据糊弄
        raise RuntimeError(f"获取视频列表失败（WBI/legacy 均失败）: {errors[-1] if errors else 'unknown'}")


def _get_user_videos_legacy(mid: int, page: int = 1, ps: int = 30) -> BiliUserVideos:
    data = _cached_request(
        "https://api.bilibili.com/x/space/arc/search",
        {"mid": mid, "ps": ps, "pn": page, "order": "pubdate"},
        ttl=settings.bili_video_list_cache_ttl,
        extra_headers={"Referer": f"https://space.bilibili.com/{mid}"},
    )
    vlist = data["data"].get("list", {}).get("vlist", [])
    videos: List[BiliVideoItem] = []
    for item in vlist:
        videos.append(BiliVideoItem(
            bvid=item.get("bvid", ""), title=_clean_title(item.get("title", "")),
            author=item.get("author", ""), author_mid=mid,
            pic=item.get("pic", ""), duration=_format_duration(item.get("length")),
            description=item.get("description", ""), play_count=item.get("play"),
            pubdate=_format_pubdate(item.get("created", 0)),
        ))
    return BiliUserVideos(videos=videos, total=data["data"].get("page", {}).get("count", 0))


def _parse_bili_count(text) -> int:
    """解析B站播放数文本，如 '28.3万' -> 283000, '1.2亿' -> 120000000"""
    if isinstance(text, int):
        return text
    if not text or not isinstance(text, str):
        return 0
    text = text.strip()
    try:
        if '亿' in text:
            return int(float(text.replace('亿', '')) * 100000000)
        elif '万' in text:
            return int(float(text.replace('万', '')) * 10000)
        else:
            return int(text)
    except (ValueError, TypeError):
        return 0


def _get_user_videos_from_dynamic(mid: int, page: int = 1, ps: int = 30) -> BiliUserVideos:
    """从用户动态流中提取视频信息（作为最后备选方案）"""
    params = {
        "host_mid": mid,
        "time": 0,
        "platform": "web",
        "web_location": "1550101",
    }
    data = _cached_request(
        "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space",
        params, ttl=settings.bili_video_list_cache_ttl,
        extra_headers={"Referer": f"https://space.bilibili.com/{mid}"},
    )
    items = data.get("data", {}).get("items", [])
    videos: List[BiliVideoItem] = []
    for item in items:
        modules = item.get("modules", {})
        # 作者信息从 modules_author 获取
        modules_author = modules.get("module_author", {})
        author_name = modules_author.get("name", "")
        author_mid = modules_author.get("mid", mid)
        pub_ts = modules_author.get("pub_ts", 0)
        
        module_dynamic = modules.get("module_dynamic", {})
        if not module_dynamic:
            continue
        major = module_dynamic.get("major") or {}
        archive = major.get("archive") or {}
        if archive:
            bvid = archive.get("bvid", "")
            if bvid:
                stat = archive.get("stat", {})
                cover = archive.get("cover", "")
                # 确保 cover 是 https
                if cover.startswith("http://"):
                    cover = "https://" + cover[7:]
                videos.append(BiliVideoItem(
                    bvid=bvid,
                    title=_clean_title(archive.get("title", "")),
                    author=author_name,
                    author_mid=author_mid,
                    pic=cover,
                    duration=_format_duration(archive.get("duration_text", "")),
                    description="",
                    play_count=_parse_bili_count(stat.get("play", 0)),
                    pubdate=_format_pubdate(pub_ts),
                ))
    return BiliUserVideos(videos=videos, total=len(videos))


# ===================== 关注列表（需登录） =====================

def get_followings(page: int = 1, ps: int = 30) -> dict:
    if not bili_auth.is_logged_in():
        raise RuntimeError("请先登录B站")
    data = _cached_request(
        "https://api.bilibili.com/x/relation/followings",
        {"vmid": bili_auth.get_user_info().get("mid"), "pn": page, "ps": ps,
         "order": "desc", "order_type": "attention"},
        ttl=20,
    )
    items = data["data"].get("list", [])
    users = [{"mid": u.get("mid"), "name": u.get("uname", ""),
              "face": u.get("face", ""), "sign": u.get("sign", "")} for u in items]
    return {"users": users, "total": data["data"].get("total", 0), "page": page}


# ===================== 收藏夹（需登录） =====================

def get_favorites(page: int = 1, ps: int = 20) -> dict:
    if not bili_auth.is_logged_in():
        raise RuntimeError("请先登录B站")
    data = _cached_request(
        "https://api.bilibili.com/x/v3/fav/folder/created/list",
        {"up_mid": bili_auth.get_user_info().get("mid"), "pn": page, "ps": ps},
        ttl=20,
    )
    folders = [{"id": f.get("id"), "title": f.get("title", ""),
                "media_count": f.get("media_count", 0), "cover": f.get("cover", "")}
               for f in data["data"].get("list", [])]
    return {"folders": folders, "total": data["data"].get("count", 0)}


def get_favorite_content(media_id: int, page: int = 1, ps: int = 20) -> dict:
    if not bili_auth.is_logged_in():
        raise RuntimeError("请先登录B站")
    data = _cached_request(
        "https://api.bilibili.com/x/v3/fav/resource/list",
        {"media_id": media_id, "pn": page, "ps": ps, "platform": "web"},
        ttl=20,
    )
    videos = []
    for item in data["data"].get("medias", []):
        videos.append(BiliVideoItem(
            bvid=item.get("bvid", ""), title=_clean_title(item.get("title", "")),
            author=item.get("upper", {}).get("name", ""),
            author_mid=item.get("upper", {}).get("mid"),
            pic=item.get("cover", ""), duration=_format_duration(item.get("duration", 0)),
            description=item.get("intro", ""),
            play_count=item.get("cnt_info", {}).get("play"),
            pubdate=_format_pubdate(item.get("pubtime", 0)),
        ).model_dump())
    return {"videos": videos, "total": data["data"].get("info", {}).get("media_count", 0), "page": page}


# ===================== 历史记录（需登录） =====================

def get_history(page: int = 1, ps: int = 20) -> dict:
    if not bili_auth.is_logged_in():
        raise RuntimeError("请先登录B站")
    data = _cached_request(
        "https://api.bilibili.com/x/web-interface/history/cursor",
        {"ps": ps, "pn": page, "type": "archive"},
        ttl=20,
    )
    videos = []
    for item in data["data"].get("list", []):
        videos.append(BiliVideoItem(
            bvid=item.get("bvid", "") or item.get("history", {}).get("bvid", ""),
            title=_clean_title(item.get("title", "")),
            author=item.get("author_name", "") or item.get("owner", {}).get("name", ""),
            author_mid=item.get("author_mid") or item.get("owner", {}).get("mid"),
            pic=item.get("pic", "") or item.get("cover", ""),
            duration=_format_duration(item.get("duration", 0)),
            description=item.get("desc", ""),
            play_count=item.get("stat", {}).get("view"),
        ).model_dump())
    return {"videos": videos, "total": data["data"].get("page", {}).get("total", 0), "page": page}


# ===================== 播放地址（自建播放器用） =====================

def get_playurl(bvid: str, cid: int, qn: int = 80) -> dict:
    """获取视频播放直链地址（WBI 签名 + dm_* 指纹）

    返回可直接用于 <video> 或 DPlayer 的 MP4/FLV URL，
    流量直接走 B站 CDN，不经过本后端。

    Args:
        bvid: BV号
        cid:  分P的 cid
        qn:   清晰度，默认 80（1080P），未登录可能降级

    Returns:
        {url, quality, format, timelength, accept_quality, accept_description}
    """
    params = _sign_wbi({
        "bvid": bvid,
        "cid": cid,
        "qn": qn,
        "fnval": 1,          # FLV/MP4 单文件（不用 DASH，最省事）
        "fnver": 0,
        "fourk": 1,
        "platform": "html5",
        "web_location": "1315877",
    })

    data = _cached_request(
        "https://api.bilibili.com/x/player/wbi/playurl",
        params, ttl=3600,     # 1h：CDN URL expire 通常数小时
    )
    result = data["data"]
    durl = result.get("durl", [])

    return {
        "url": durl[0]["url"] if durl else None,
        "quality": result.get("quality"),
        "format": result.get("format"),
        "timelength": result.get("timelength"),
        "accept_quality": result.get("accept_quality", []),
        "accept_description": result.get("accept_description", []),
    }


# ====== 启动预加载 ======

def init_bili():
    """后端启动时调用：预热 session + 获取 WBI 密钥。
    避免首个用户请求在节流控制下连打 3 次 B站。"""
    logger.info("B站 预加载开始...")
    try:
        _create_session()  # 预热 session（含 visit cookies）
        _fetch_wbi_keys()  # 获取 WBI 密钥
        logger.info("B站 预加载完成 ✓")
    except Exception as e:
        logger.warning(f"B站 预加载失败（不影响使用，首次请求会自行初始化）: {e}")
