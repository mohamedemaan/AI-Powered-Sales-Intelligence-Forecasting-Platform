import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Attempt to load .env from backend/.env or root .env
try:
    from dotenv import load_dotenv
    _backend_dir = Path(__file__).resolve().parent.parent.parent
    load_dotenv(_backend_dir / ".env")
    load_dotenv(_backend_dir.parent / ".env")
except Exception:
    pass

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sales Intelligence Platform API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "DEV_SECRET_KEY_123456789"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    
    # Gemini Pro API Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    
    # Postgres configuration with local fallback defaults
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "sales_intel"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        # 1. Explicit DATABASE_URL takes highest priority (Docker / cloud platforms)
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            # Heroku-style postgres:// -> postgresql://
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            return db_url
        # 2. SQLite fallback for local dev
        if os.getenv("USE_SQLITE", "true").lower() == "true":
            return "sqlite:///./sql_app.db"
        # 3. Compose individual vars
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    class Config:
        case_sensitive = True

settings = Settings()
