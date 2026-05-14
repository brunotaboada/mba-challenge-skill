import os


def _env_bool(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).lower() in ("1", "true", "yes", "on")


def _env_list(name: str, default: str) -> list[str]:
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings:
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DEBUG: bool = _env_bool("FLASK_DEBUG", "0")
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH: str = os.environ.get("DATABASE_PATH", "loja.db")
    ALLOWED_ORIGINS: list[str] = _env_list(
        "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5000"
    )
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").upper()
    VERSION: str = "1.0.0"


settings = Settings()
