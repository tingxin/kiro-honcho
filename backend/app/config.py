"""Application configuration"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra fields in .env
    )
    
    APP_NAME: str = "Kiro Honcho"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/data/kiro_honcho.db"
    DB_SSL_CA: Optional[str] = None
    
    # JWT Settings
    SECRET_KEY: str = "your-super-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Alias for .env compatibility
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    
    # Encryption key for AWS credentials (32 bytes for AES-256)
    ENCRYPTION_KEY: str = "your-32-byte-encryption-key-here"
    APP_ENCRYPTION_KEY: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5020,http://localhost:5173"
    
    # Default credentials
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"
    
    # 自动订阅检查间隔（分钟），0 表示不检查
    AUTO_SUBSCRIBE_CHECK_INTERVAL: int = 5
    
    # AWS Defaults
    DEFAULT_SSO_REGION: str = "us-east-1"
    DEFAULT_KIRO_REGION: str = "us-east-1"
    
    def get_secret_key(self) -> str:
        """Get the effective secret key."""
        return self.JWT_SECRET_KEY or self.SECRET_KEY
    
    def get_encryption_key(self) -> str:
        """Get the effective encryption key."""
        return self.APP_ENCRYPTION_KEY or self.ENCRYPTION_KEY
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()


# Legacy exports for backward compatibility
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR}/data/kiro_honcho.db")
SECRET_KEY = os.getenv("SECRET_KEY", os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production-min-32-chars"))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", os.getenv("APP_ENCRYPTION_KEY", "your-32-byte-encryption-key-here"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5020,http://localhost:5173").split(",")
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
