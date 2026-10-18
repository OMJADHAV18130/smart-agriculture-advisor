"""
Configuration settings for the Smart Agriculture Advisory backend.
Loads settings from environment variables and an optional .env file.
"""

import os
from pathlib import Path
from typing import List

# Attempt to load .env if python-dotenv is available
try:
    from dotenv import load_dotenv

    # Find .env in backend directory or parent directory
    backend_env = Path(__file__).resolve().parent.parent / ".env"
    root_env = Path(__file__).resolve().parent.parent.parent / ".env"

    if backend_env.exists():
        load_dotenv(dotenv_path=backend_env)
    elif root_env.exists():
        load_dotenv(dotenv_path=root_env)
    else:
        load_dotenv()  # Fallback to current working directory
except ImportError:
    pass


def parse_origins(raw_origins: str) -> List[str]:
    """Parse comma-separated origins string into a list of cleaned origin strings."""
    if not raw_origins:
        return []
    raw_origins = raw_origins.strip()
    if raw_origins == "*":
        return ["*"]
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


class Settings:
    def __init__(self) -> None:
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info").lower()

        # CORS origins: comma-separated list or '*'
        raw_origins = os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        )
        self.ALLOWED_ORIGINS: List[str] = parse_origins(raw_origins)

        # Dataset file path override
        custom_data_path = os.getenv("DATASET_PATH")
        if custom_data_path:
            self.DATA_FILE_PATH: Path = Path(custom_data_path)
        else:
            self.DATA_FILE_PATH: Path = (
                Path(__file__).resolve().parent.parent / "data" / "cleaned_crop_recommendation.csv"
            )


settings = Settings()
