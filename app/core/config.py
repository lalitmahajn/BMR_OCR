from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "BMR Document Intelligence Engine"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    TEMPLATE_DIR: Path = BASE_DIR / "templates"

    # Database (SQLite for now, easy switch to Postgres)
    DATABASE_URL: str = "sqlite:///./sql_app.db"

    # Engine Settings
    OCR_ENABLED: bool = True
    DEBUG_MODE: bool = False

    # Mistral OCR
    MISTRAL_API_KEY: Optional[str] = None
    OCR_ENGINE: str = "paddle"
    MISTRAL_MODEL: str = "mistral-ocr-latest"
    MISTRAL_TIMEOUT: int = 30
    MISTRAL_MAX_RETRIES: int = 3

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
