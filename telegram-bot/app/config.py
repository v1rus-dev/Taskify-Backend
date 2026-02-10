import os


def _parse_chat_ids(raw_value: str | None) -> set[int]:
    if not raw_value:
        return set()

    chat_ids: set[int] = set()
    for part in raw_value.split(","):
        value = part.strip()
        if not value:
            continue
        try:
            chat_ids.add(int(value))
        except ValueError:
            continue
    return chat_ids


class Settings:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    api_key = os.getenv("TELEGRAM_BOT_GATEWAY_API_KEY", "").strip()
    chat_ids = _parse_chat_ids(os.getenv("TELEGRAM_CHAT_IDS"))
    metrics_disk_path = os.getenv("TELEGRAM_METRICS_DISK_PATH", "/hostfs").strip() or "/"
