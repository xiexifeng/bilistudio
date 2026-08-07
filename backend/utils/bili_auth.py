"""
B站扫码登录管理器
- 生成二维码 → 轮询扫码状态 → 存储cookie到文件
- 后续所有B站API请求自动携带登录态

关键：必须使用同一个 requests.Session 贯穿 generate + poll，
      否则 cookie 无法累积，导致登录失败。
"""
import json
import time
import threading
from pathlib import Path
from typing import Optional, Dict
import requests

# Cookie 持久化文件
COOKIE_FILE = Path(__file__).parent.parent / ".bili_cookies.json"

# 请求头（模拟浏览器）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.bilibili.com/",
}

# 全局状态
_lock = threading.Lock()
_cookies: Dict[str, str] = {}
_user_info: Optional[Dict] = None
_pending_qr: Optional[Dict] = None  # 当前有效的二维码
_qr_session: Optional[requests.Session] = None  # 扫码专用session


def _load_cookies():
    """从文件加载cookie"""
    global _cookies
    try:
        if COOKIE_FILE.exists():
            _cookies = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
            return True
    except Exception:
        pass
    return False


def _save_cookies():
    """保存cookie到文件"""
    COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
    COOKIE_FILE.write_text(json.dumps(_cookies, ensure_ascii=False, indent=2), encoding="utf-8")


# 启动时加载已有cookie
_load_cookies()


def get_cookies() -> Dict[str, str]:
    """获取当前B站登录cookie"""
    with _lock:
        return dict(_cookies)


def get_cookie_string() -> str:
    """获取cookie字符串（用于请求头）"""
    with _lock:
        return "; ".join(f"{k}={v}" for k, v in _cookies.items())


def is_logged_in() -> bool:
    """检查是否有有效的B站登录态"""
    with _lock:
        return bool(_cookies.get("SESSDATA"))


def get_user_info() -> Optional[Dict]:
    """获取已缓存的B站用户信息"""
    with _lock:
        return dict(_user_info) if _user_info else None


def clear_login():
    """清除B站登录态"""
    global _cookies, _user_info, _qr_session
    with _lock:
        _cookies = {}
        _user_info = None
    _qr_session = None
    try:
        COOKIE_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def generate_qrcode() -> Dict:
    """
    生成B站登录二维码
    返回: { "url": "二维码链接", "qrcode_key": "轮询key" }
    """
    global _pending_qr, _qr_session

    # 创建新的扫码session，后续poll要用同一个session才能累积cookie
    _qr_session = requests.Session()
    _qr_session.headers.update(HEADERS)

    url = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
    resp = _qr_session.get(url, timeout=10)
    data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"获取二维码失败: {data.get('message', 'unknown')}")

    qr_data = data["data"]
    result = {
        "url": qr_data["url"],
        "qrcode_key": qr_data["qrcode_key"],
    }

    with _lock:
        _pending_qr = result

    return result


def poll_qrcode(qrcode_key: str) -> Dict:
    """
    轮询扫码状态
    返回: {
        "status": "pending" | "scanned" | "success" | "expired",
        "message": "提示文字",
        "user": { "name": "...", "face": "..." }  (仅success时)
    }
    """
    global _cookies, _user_info, _qr_session

    if _qr_session is None:
        return {"status": "error", "message": "二维码session已过期，请重新获取"}

    url = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
    params = {"qrcode_key": qrcode_key}

    resp = _qr_session.get(url, params=params, timeout=10)
    data = resp.json()

    code = data.get("data", {}).get("code")

    if code == 86101:
        return {"status": "pending", "message": "等待扫码..."}

    elif code == 86090:
        return {"status": "scanned", "message": "已扫码，请在手机上确认登录"}

    elif code == 0:
        # 登录成功！
        # 先访问返回的 url（如果有），以获取完整的跨域cookie
        redirect_url = data.get("data", {}).get("url")
        if redirect_url:
            try:
                _qr_session.get(redirect_url, headers=HEADERS, timeout=15, allow_redirects=True)
            except Exception:
                pass  # 即使失败，session里可能已经有足够cookie

        # 再访问B站首页，确保cookie完整
        try:
            _qr_session.get("https://www.bilibili.com/", headers=HEADERS, timeout=10)
        except Exception:
            pass

        # 提取session中所有cookie
        all_cookies = _qr_session.cookies.get_dict()

        with _lock:
            _cookies = all_cookies

        _save_cookies()
        _qr_session = None  # 清理session

        # 获取用户信息
        try:
            user_data = _fetch_bili_user_info()
            with _lock:
                _user_info = user_data
        except Exception:
            user_data = {"name": "B站用户", "face": ""}

        return {
            "status": "success",
            "message": "登录成功！",
            "user": user_data,
        }

    elif code == 86038:
        return {"status": "expired", "message": "二维码已过期，请重新获取"}

    else:
        return {"status": "error", "message": data.get("message", "未知错误")}


def _fetch_bili_user_info() -> Dict:
    """获取B站当前登录用户信息"""
    url = "https://api.bilibili.com/x/web-interface/nav"

    resp = requests.get(
        url,
        headers={**HEADERS, "Cookie": get_cookie_string()},
        timeout=10,
    )
    data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"获取用户信息失败: {data.get('message')}")

    user = data["data"]
    return {
        "mid": user.get("mid"),
        "name": user.get("uname", ""),
        "face": user.get("face", ""),
        "level": user.get("level_info", {}).get("current_level", 0),
    }


def refresh_user_info():
    """手动刷新用户信息"""
    global _user_info
    try:
        user_data = _fetch_bili_user_info()
        with _lock:
            _user_info = user_data
        return user_data
    except Exception as e:
        raise RuntimeError(f"刷新用户信息失败: {e}")
