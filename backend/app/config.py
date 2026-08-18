import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    DATABASE_URL: str = "sqlite:///./maruthi.db"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_SECRET_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
