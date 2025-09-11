# Store Bot – Render FREE Web Service

Эта версия запускает бота как **Web Service** (бесплатный план Render). Внутри есть маленький HTTP‑сервер для health‑check на `$PORT`.

## Render (Free)
1) Подключи репозиторий к Render как **Blueprint** — `render.yaml` создаст Web Service.
2) Задай `BOT_TOKEN` и `ADMIN_IDS` в Environment.
3) Deploy. Сервис будет слушать `$PORT` и параллельно запускать Telegram‑бота.

## Локально
```
cp .env.example .env
docker compose up --build
```
Открой http://localhost:8080/ — увидишь статус. В Телеграме проверь `/start`.
