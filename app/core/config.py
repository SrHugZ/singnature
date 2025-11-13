from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Signatures Platform API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "mysql+pymysql://signatures_user:signatures_pass@db:3306/signatures_db"
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-characters-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Debug
    DEBUG: bool = True
    
    # SMTP
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Uploads
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE: int = 5242880

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"


settings = Settings()