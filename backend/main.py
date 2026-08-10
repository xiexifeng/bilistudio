import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from database import engine, Base
from pydantic import BaseModel
from routers import bilibili, collection, auth, users, stats, courses
from config import settings
from utils.logger import setup_logging

# ---- 初始化日志系统 ----
setup_logging(log_file=settings.log_file, level=settings.log_level)
logger = logging.getLogger("bilistudio")


def _migrate_db():
    """轻量级数据库迁移（适用于 SQLite 新增字段）"""
    with engine.connect() as conn:
        # 检查并添加 collection 表的新字段
        result = conn.execute(text("PRAGMA table_info(collection)"))
        cols = {row[1] for row in result}

        if "user_id" not in cols:
            conn.execute(text("ALTER TABLE collection ADD COLUMN user_id INTEGER DEFAULT 1"))
            logger.info("迁移: collection 添加 user_id 列")
        if "status" not in cols:
            conn.execute(text("ALTER TABLE collection ADD COLUMN status VARCHAR(20) DEFAULT 'todo'"))
            logger.info("迁移: collection 添加 status 列")
        if "watch_progress" not in cols:
            conn.execute(text("ALTER TABLE collection ADD COLUMN watch_progress INTEGER DEFAULT 0"))
            logger.info("迁移: collection 添加 watch_progress 列")
        conn.commit()

        # 移除 bvid 的唯一约束（改为 user_id + bvid 组合唯一）
        try:
            indexes = conn.execute(text("PRAGMA index_list(collection)"))
            for idx in indexes:
                if idx[1] and "bvid" in idx[1]:
                    # 尝试删除旧的唯一索引
                    try:
                        conn.execute(text(f"DROP INDEX IF EXISTS {idx[1]}"))
                    except Exception:
                        pass
            conn.commit()
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables + migration
    Base.metadata.create_all(bind=engine)
    _migrate_db()

    # 确保默认用户存在
    from database import SessionLocal
    from models import User as UserModel
    import random
    db = SessionLocal()
    try:
        user = db.query(UserModel).filter(UserModel.id == 1).first()
        if not user:
            _names = ["小明", "小方", "小华", "小美", "小丽", "小龙", "小虎", "小兔", "小星", "小月"]
            _colors = ["#FF6B35", "#45B7D1", "#10B981", "#8B5CF6", "#F59E0B", "#EC4899", "#6366F1", "#14B8A6"]
            user = UserModel(id=1, name=random.choice(_names), color=random.choice(_colors))
            db.add(user)
            db.commit()
            logger.info(f"创建默认用户: {user.name}")
    finally:
        db.close()

    logger.info("数据库初始化完成")

    # 预热 B站 session + WBI 密钥
    from utils.bili_api import init_bili
    init_bili()
    yield
    # Shutdown
    logger.info("服务关闭")

app = FastAPI(
    title="BiliStudio API",
    version="2.0.0",
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

app.include_router(auth.router, prefix="/api")
app.include_router(bilibili.router, prefix="/api")
app.include_router(collection.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(courses.router, prefix="/api")

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
