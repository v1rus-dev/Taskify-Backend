# Telegram Bot Gateway

Сервис запускается как контейнер `telegram-bot` и выполняет две задачи:

1. Принимает критические алерты от backend через HTTP.
2. Отвечает в Telegram командами `/status` и `/disk` для проверки сервера.

## Переменные окружения

- `TELEGRAM_BOT_TOKEN` - токен Telegram-бота (обязательно).
- `TELEGRAM_CHAT_IDS` - список chat_id через запятую, куда слать алерты.
- `TELEGRAM_BOT_GATEWAY_API_KEY` - API ключ для `POST /api/v1/notify`.
- `TELEGRAM_METRICS_DISK_PATH` - путь для проверки диска, по умолчанию `/hostfs`.
- `TELEGRAM_BOT_GATEWAY_URL` - URL в backend для отправки алертов в gateway.
- `TELEGRAM_ALERTS_ENABLED` - `true/false` переключатель отправки алертов из backend.
- `INTERNAL_ALERTS_API_KEY` - ключ защиты backend endpoint `/internal/alerts/critical`.

## Отправка алерта из backend

Backend endpoint:

`POST /internal/alerts/critical`

Пример запроса:

```bash
curl -X POST http://localhost:8000/internal/alerts/critical \
  -H "Content-Type: application/json" \
  -H "X-Internal-Key: YOUR_INTERNAL_ALERTS_API_KEY" \
  -d '{
    "title": "DB timeout",
    "message": "Database is not responding for 30s",
    "source": "taskify-backend",
    "tags": ["db", "prod"],
    "details": {"region": "eu-central-1", "attempts": 5}
  }'
```
