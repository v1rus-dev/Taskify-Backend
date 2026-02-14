import os


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT', 5432)}/"
    f"{os.getenv('POSTGRES_DB')}"
)

TELEGRAM_ALERTS_ENABLED = _as_bool(os.getenv("TELEGRAM_ALERTS_ENABLED"), default=True)
TELEGRAM_BOT_GATEWAY_URL = os.getenv("TELEGRAM_BOT_GATEWAY_URL", "http://telegram-bot:8082/api/v1/notify")
TELEGRAM_BOT_GATEWAY_API_KEY = os.getenv("TELEGRAM_BOT_GATEWAY_API_KEY", "")
TELEGRAM_REQUEST_TIMEOUT_SECONDS = _as_float(os.getenv("TELEGRAM_REQUEST_TIMEOUT_SECONDS"), default=5.0)
INTERNAL_ALERTS_API_KEY = os.getenv("INTERNAL_ALERTS_API_KEY", "")
