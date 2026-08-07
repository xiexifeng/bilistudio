"""
统一日志模块：同时输出到控制台和文件。
日志文件路径通过 config.settings.log_file 配置，默认 ./logs/bilistudio.log
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

LOG_FORMAT = "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_initialized = False


def setup_logging(log_file: str = "", level: str = "INFO"):
    """初始化全局日志系统。只需调用一次，重复调用不会重复添加 handler。"""
    global _initialized
    if _initialized:
        return

    # 取目标级别
    log_level = getattr(logging, level.upper(), logging.INFO)

    # 重置 root logger
    root = logging.getLogger()
    root.setLevel(log_level)

    # 先清掉已有的 handler（uvicorn 可能自带）
    root.handlers.clear()

    # ---- 控制台 ----
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(log_level)
    console.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root.addHandler(console)

    # ---- 文件（轮转，单文件最大 10MB，保留 3 个备份）----
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            str(log_path), maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        root.addHandler(file_handler)

    # 抑制过于啰嗦的第三方 logger
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    _initialized = True

    logger = logging.getLogger("bilistudio")
    logger.info(f"日志系统初始化完成 level={level} file={log_file or '(仅控制台)'}")
