"""Environment-aware application settings."""
from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parents[2]
ENV_FILES = {"local": ".env.local", "dev": ".env.local", "prod": ".env.prod"}
APP_ENV = os.getenv("APP_ENV", "local").lower()
if APP_ENV not in ENV_FILES:
    raise RuntimeError("APP_ENV must be one of: local, dev, prod.")
load_dotenv(PROJECT_DIR / ENV_FILES[APP_ENV], override=False)

DEFAULTS = {
    "local": {"host": "127.0.0.1", "debug": True, "history": "data/chat_history.local.db"},
    "dev": {"host": "127.0.0.1", "debug": True, "history": "data/chat_history.dev.db"},
    "prod": {"host": "0.0.0.0", "debug": False, "history": "data/chat_history.prod.db"},
}
DEFAULT_CORS = {
    "local": "http://localhost:3002,http://127.0.0.1:3002,http://localhost:8003,http://127.0.0.1:8003",
    "dev": "http://localhost:3002,http://127.0.0.1:3002,http://localhost:8003,http://127.0.0.1:8003",
    "prod": "",
}


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    host: str
    port: int
    debug: bool
    log_level: str
    cors_origins: tuple[str, ...]
    gemini_api_key: str | None
    gemini_model_name: str
    gemini_fallback_models: tuple[str, ...]
    app_database_url: str | None
    target_database_url: str | None


def load_settings() -> Settings:
    defaults = DEFAULTS[APP_ENV]
    return Settings(
        app_name=os.getenv("APP_NAME", "DB Gemini Assistant"), app_env=APP_ENV,
        host=os.getenv("APP_HOST", defaults["host"]), port=int(os.getenv("APP_PORT", "3002")),
        debug=_as_bool(os.getenv("APP_DEBUG", str(defaults["debug"]))),
        log_level=os.getenv("LOG_LEVEL", "DEBUG" if defaults["debug"] else "INFO").upper(),
        cors_origins=_csv(os.getenv("CORS_ORIGINS", DEFAULT_CORS[APP_ENV])),
        gemini_api_key=os.getenv("GEMINI_API_KEY"), gemini_model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-3.6-flash"),
        gemini_fallback_models=_csv(os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.5-flash-lite")),
        app_database_url=os.getenv("APP_DATABASE_URL"),
        # DATABASE_URL remains a temporary backwards-compatible alias.
        target_database_url=os.getenv("TARGET_DATABASE_URL", os.getenv("DATABASE_URL")),
    )


settings = load_settings()
