from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "*"]

    # Neon PostgreSQL Database (Single Source of Truth)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/flight_management"

    # JWT Authentication
    JWT_SECRET: str = "super-secret-jwt-key-replace-in-production-flight-system-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Business Rules Defaults
    SEAT_HOLD_DURATION_MINUTES: int = 10

    # n8n Automation Webhook Coordination
    N8N_BASE_URL: str = "https://smithackathon.app.n8n.cloud"
    N8N_WEBHOOK_URL: Optional[str] = "https://smithackathon.app.n8n.cloud/webhook/flight-events"
    N8N_WEBHOOK_SECRET: str = "smithackathon_secret_token_2026"

    # ChromaDB Vector Store
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"

    # Groq LLM API Key & Model
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
