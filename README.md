# Store Bot – Plug & Play (No Payments)

Готовый репозиторий. Ничего копировать не нужно — просто залей архив в GitHub/Render/Railway.

## Вариант A — Render (рекомендуется)
1. Импортируй этот репозиторий на Render (или загрузь ZIP прямо).
2. Render сам увидит `render.yaml`. Укажи переменные окружения: `BOT_TOKEN`, `ADMIN_IDS`.
3. Нажми Deploy. Диск уже подключен (mountPath `/app`) — база и экспорт сохраняются.

## Вариант B — Railway
1. Импортируй в Railway репозиторий (или ZIP).
2. Railway прочитает `Railway.toml`. Укажи `BOT_TOKEN`, `ADMIN_IDS` в Variables.
3. Deploy.

## Вариант C — Docker Compose (локально)
1. Создай `.env` из `.env.example` и заполни токен и админов.
2. Запусти: `docker compose up --build`

## Что внутри
- Каталог → корзина → оформление (без оплаты)
- Динамический курс
- Админка: курс, каталог JSON, заказы, экспорт CSV
- Авто-экспорт каждые Пн 09:00 (Europe/Moscow)
- SQLite хранится рядом: `store.db`, выгрузки — в `exports/`

Команды в чате:
- `/start` — меню
- `/admin` — админка (только для ID из `ADMIN_IDS`)
