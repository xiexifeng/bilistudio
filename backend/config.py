from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MySQL
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "bilistudio"

    # JWT
    secret_key: str = "bilistudio-secret-key-change-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # App
    app_password: str = "123456"  # 单用户模式默认密码

    # 日志
    log_level: str = "INFO"              # DEBUG / INFO / WARNING / ERROR
    log_file: str = "./logs/bilistudio.log"

    # B站 API 频率控制
    bili_min_interval: float = 5.0      # 两次请求最小间隔（秒），默认5秒 + 抖动
    bili_retry_count: int = 3            # -799 自动重试次数
    bili_search_cache_ttl: int = 60      # 搜索缓存秒数
    bili_video_list_cache_ttl: int = 600 # UP主视频列表缓存秒数（10分钟，视频列表变化慢）

    class Config:
        env_file = ".env"

settings = Settings()
