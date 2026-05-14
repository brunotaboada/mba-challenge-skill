import os


def _env_bool(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).lower() in ("1", "true", "yes", "on")


class Settings:
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DEBUG: bool = _env_bool("FLASK_DEBUG", "0")
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
    ALLOWED_ORIGINS: list[str] = [
        s.strip()
        for s in os.environ.get(
            "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5000"
        ).split(",")
        if s.strip()
    ]
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").upper()
    JWT_EXPIRES_MINUTES: int = int(os.environ.get("JWT_EXPIRES_MINUTES", "60"))

    NOTIFICATIONS_ENABLED: bool = _env_bool("NOTIFICATIONS_ENABLED", "0")
    SMTP_HOST: str = os.environ.get("SMTP_HOST", "")
    SMTP_PORT: int = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER: str = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD: str = os.environ.get("SMTP_PASSWORD", "")


settings = Settings()
