from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    APP_NAME: str = "AI Document Screening System"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Defaults to SQLite for zero-config; set DATABASE_URL to a
    # postgresql:// URL in production (e.g. postgresql://user:pass@host/db)
    DATABASE_URL: str = "sqlite:///./screening.db"
    
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Risk scoring weights
    TAMPERING_WEIGHT: float = 0.4
    VALIDATION_WEIGHT: float = 0.3
    FACE_MATCH_WEIGHT: float = 0.3
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
