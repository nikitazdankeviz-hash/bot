# Store Bot – Webhook mode (Render FREE, no polling conflicts)

Эта версия работает через **webhook** (Telegram шлёт апдейты на ваш URL). Конфликтов `getUpdates` нет.

## Шаги на Render
1. Подключите репозиторий → Blueprint (Web Service).
2. В Environment задайте:
   - `BOT_TOKEN` – токен бота
   - `ADMIN_IDS` – ваш Telegram ID
   - `WEBHOOK_BASE` – адрес сервиса: `https://<your>.onrender.com`
3. Deploy. Зайдите на `/` — увидите JSON-статус.

## Примечания
- При старте сервис сам выставляет вебхук `WEBHOOK_BASE + /tg/<bot_id>`.
- При остановке удаляет вебхук.
- Для локального теста можно запустить с ngrok и выставить `WEBHOOK_BASE` на публичный https URL.
