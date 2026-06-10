import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "OSCA - Open Source Contribution Agent"
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
    GITHUB_REDIRECT_URI: str = os.getenv(
        "GITHUB_REDIRECT_URI", "http://localhost:8000/api/v1/auth/callback"
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))  # 7 days
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500/frontend/index.html")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./osca_platform.db")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    ENABLE_GEMINI_EXPLANATIONS: bool = os.getenv("ENABLE_GEMINI_EXPLANATIONS", "true").lower() == "true"


settings = Settings()
