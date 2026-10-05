import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "DermIA API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dermia-super-secret-key-change-in-production-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days for community workers
    
    # Database (SQLite by default for zero-friction setup, PostgreSQL ready)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./dermia.db"
    )
    
    # Storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./storage/uploads")
    MODEL_DIR: str = os.getenv("MODEL_DIR", "../ml/export")
    KB_DIR: str = os.getenv("KB_DIR", "../knowledge_base")
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    
    class Config:
        case_sensitive = True

settings = Settings()
