"""DWH-Generator 后端配置"""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "DWH-Generator"
    app_version: str = "1.0.0"
    debug: bool = True

    # 密码加密密钥（生产环境应从环境变量读取）
    secret_key: str = "dwh-generator-secret-key-change-in-production"

    # META 库（SQLite，本地文件，自动创建）
    # 路径相对于 config.py 所在目录 (backend/app/)，定位到 backend/data/
    meta_db_path: str = str(Path(__file__).resolve().parent.parent / "data" / "meta.db")

    # CORS 允许的前端地址
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Alias environment variable names to match .env
        # (pydantic-settings v2 auto-maps by case-insensitive name)
        extra = "ignore"


settings = Settings()