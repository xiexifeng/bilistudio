import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import engine, Base
from pydantic import BaseModel
from routers import bilibili, collection, auth
from config import settings
from utils.logger import setup_logging

# ---- 初始化日志系统 ----
setup_logging(log_file=settings.log_file, level=settings.log_level)
logger = logging.getLogger("bilistudio")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表创建完成")
    # 预热 B站 session + WBI 密钥
    from utils.bili_api import init_bili
    init_bili()
    yield
    # Shutdown
    logger.info("服务关闭")

app = FastAPI(
    title="BiliStudio API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(bilibili.router)
app.include_router(collection.router)

# ===== 请求日志中间件 =====

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = (time.time() - start) * 1000
    logger.info(
        f"HTTP {request.method} {request.url.path}?{request.url.query} "
        f"→ {response.status_code} ({elapsed:.0f}ms)"
    )
    return response

@app.get("/")
def root():
    return {"msg": "BiliStudio API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

# ====== 频率控制配置 ======

class RateConfig(BaseModel):
    bili_min_interval: float
    bili_retry_count: int
    bili_search_cache_ttl: int

@app.get("/api/config/rate")
def get_rate_config():
    """查看当前 B站 API 频率限制参数"""
    return RateConfig(
        bili_min_interval=settings.bili_min_interval,
        bili_retry_count=settings.bili_retry_count,
        bili_search_cache_ttl=settings.bili_search_cache_ttl,
    )

@app.post("/api/config/rate")
def update_rate_config(cfg: RateConfig):
    """调整 B站 API 频率限制参数（重启后重置为配置文件默认值）"""
    settings.bili_min_interval = max(0.5, min(cfg.bili_min_interval, 10.0))
    settings.bili_retry_count = max(1, min(cfg.bili_retry_count, 5))
    settings.bili_search_cache_ttl = max(10, min(cfg.bili_search_cache_ttl, 300))
    return {
        "msg": "已更新",
        "bili_min_interval": settings.bili_min_interval,
        "bili_retry_count": settings.bili_retry_count,
        "bili_search_cache_ttl": settings.bili_search_cache_ttl,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
