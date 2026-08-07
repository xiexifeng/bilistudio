"""
B站扫码登录接口
"""
from fastapi import APIRouter, HTTPException
from utils import bili_auth
from utils.bili_api import reset_session_cache

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/qrcode")
def get_qrcode():
    """获取B站登录二维码"""
    try:
        return bili_auth.generate_qrcode()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/qrcode/status")
def poll_qrcode(qrcode_key: str):
    """轮询B站扫码状态"""
    try:
        result = bili_auth.poll_qrcode(qrcode_key)
        if result.get("status") == "success":
            reset_session_cache()  # 登录成功，刷新session
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
def login_status():
    """查询当前B站登录状态"""
    user = bili_auth.get_user_info()
    logged_in = bili_auth.is_logged_in()
    return {"logged_in": logged_in, "user": user}


@router.post("/logout")
def logout():
    """登出B站"""
    bili_auth.clear_login()
    reset_session_cache()
    return {"ok": True}
