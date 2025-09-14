"""
Telegram bot for Zdankevich Store
=================================

This script implements a simple Telegram bot for handling purchases of in‑game
currency, games and subscriptions. The bot greets new users, offers menu
options via inline keyboards and notifies the store owner whenever a user
requests a game or subscription or confirms a coin purchase.

Key features
------------

* Greets the user as soon as they start interacting with the bot using a
  predefined welcome message.
* Presents three primary actions via inline buttons: buy coins, buy games
  and buy subscriptions.
* When a user chooses to buy coins they pick a platform (Xbox, PlayStation
  or PC) and enter the quantity of coins they want. The bot calculates the
  total cost based on a configurable rate and prompts the user to confirm
  the order.
* Upon confirmation of a coin order or selection of a game or subscription
  the bot sends a notification to the administrator (store owner) with the
  user’s details and order information.
* Provides a simple admin panel accessible to the administrator via the
  ``/admin`` command. From there the administrator can view or change the
  exchange rates for each platform.

The bot relies solely on the Telegram Bot HTTP API via the ``requests``
library and does not require any third‑party Telegram SDKs. It stores
configuration data (such as coin exchange rates) in a JSON file on disk.

Usage
-----

Set two environment variables before running the script:

``TELEGRAM_BOT_TOKEN``
    The token provided by BotFather for your Telegram bot.

``TELEGRAM_ADMIN_ID``
    Your personal Telegram user ID. The bot uses this ID to send
    administrative notifications and to grant you access to the admin panel.

To start the bot simply run the script:

```
python bot.py
```

The bot will poll for updates and respond accordingly. To stop it press
``Ctrl+C``.

Note
----

This script uses long polling and runs in a blocking loop. To deploy it in
production consider wrapping it in a service or supervisor and handling
network errors more gracefully.
"""

import json
import os
import time
from typing import Any, Dict, Optional

import requests


# Environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")

if not TOKEN:
    raise RuntimeError(
        "Environment variable TELEGRAM_BOT_TOKEN is not set. "
        "Set this variable to your bot's token before running the script."
    )
if not ADMIN_ID:
    raise RuntimeError(
        "Environment variable TELEGRAM_ADMIN_ID is not set. "
        "Set this variable to your Telegram user ID before running the script."
    )

try:
    ADMIN_ID_INT = int(ADMIN_ID)
except ValueError:
    raise RuntimeError(
        "TELEGRAM_ADMIN_ID must be an integer representing your Telegram user ID."
    )


# Data file for storing coin rates. The file is created automatically if
# absent. Rates represent the price in rubles for 1,000,000 coins on each
# platform.
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")


def load_data() -> Dict[str, Any]:
    """Load persistent data from disk.

    Returns a dictionary containing at least a ``coin_rates`` key. If the
    file does not exist it is created with default values.
    """
    if not os.path.exists(DATA_FILE):
        # Default rates in rubles per million coins
        data = {"coin_rates": {"Xbox": 10000.0, "PlayStation": 10000.0, "PC": 10000.0}}
        save_data(data)
        return data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # In case the file is corrupt, reinitialise with defaults
            data = {"coin_rates": {"Xbox": 10000.0, "PlayStation": 10000.0, "PC": 10000.0}}
            save_data(data)
            return data


def save_data(data: Dict[str, Any]) -> None:
    """Persist data to disk as JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def send_message(chat_id: int, text: str, reply_markup: Optional[Dict[str, Any]] = None) -> None:
    """Send a text message to a user via Telegram.

    Args:
        chat_id: The unique identifier of the target chat.
        text: The message text.
        reply_markup: Optional dictionary describing an inline keyboard or other
            reply markup.
    """
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload: Dict[str, Any] = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        # Serialise reply markup to JSON as required by the API
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(url, data=payload, timeout=10)
    except requests.RequestException:
        # In a production deployment you might log this or retry later.
        pass


def answer_callback_query(callback_query_id: str, text: Optional[str] = None) -> None:
    """Acknowledge a callback query so Telegram stops showing the loading spinner.

    Args:
        callback_query_id: Identifier of the callback query to answer.
        text: Optional text to display as a toast notification.
    """
    url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
    payload: Dict[str, Any] = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    try:
        requests.post(url, data=payload, timeout=10)
    except requests.RequestException:
        pass


def send_welcome(chat_id: int) -> None:
    """Send a greeting message with the main menu.

    The greeting explains what the bot can do and presents buttons for the
    primary actions: buying coins, games or subscriptions.
    """
    welcome_text = (
        "Привет, это Zdankevich Store! "
        "Я помогу тебе доставить монеты на твой аккаунт безопасно и быстро! "
        "А также я могу купить для тебя нужную игру или подписку на твою консоль!"
    )
    menu = {
        "inline_keyboard": [
            [{"text": "Купить монеты", "callback_data": "buy_coins"}],
            [{"text": "Купить игры", "callback_data": "buy_games"}],
            [{"text": "Купить подписки", "callback_data": "buy_subscriptions"}],
        ]
    }
    send_message(chat_id, welcome_text, reply_markup=menu)


def send_platforms(chat_id: int) -> None:
    """Prompt the user to select a platform for coin purchases."""
    keyboard = {
        "inline_keyboard": [
            [{"text": "Xbox", "callback_data": "platform_Xbox"}],
            [{"text": "PlayStation", "callback_data": "platform_PlayStation"}],
            [{"text": "ПК", "callback_data": "platform_PC"}],
        ]
    }
    send_message(chat_id, "Выберите платформу:", reply_markup=keyboard)


def show_admin_menu(chat_id: int) -> None:
    """Display the administrative menu to the admin user."""
    admin_keyboard = {
        "inline_keyboard": [
            [{"text": "Показать курсы", "callback_data": "admin_show_rates"}],
            [{"text": "Установить курс для Xbox", "callback_data": "admin_set_Xbox"}],
            [{"text": "Установить курс для PlayStation", "callback_data": "admin_set_PlayStation"}],
            [{"text": "Установить курс для ПК", "callback_data": "admin_set_PC"}],
            [{"text": "Назад", "callback_data": "admin_back"}],
        ]
    }
    send_message(chat_id, "Админ‑панель. Выберите действие:", reply_markup=admin_keyboard)


def handle_update(update: Dict[str, Any], data: Dict[str, Any], state: Dict[int, Dict[str, Any]]) -> None:
    """Handle a single update from the Telegram API.

    Args:
        update: The update object from getUpdates.
        data: Persistent storage including coin rates.
        state: A mapping of chat IDs to conversation state.
    """
    # Messages sent by users
    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        text = message.get("text", "")

        # Initialise state entry if absent
        if chat_id not in state:
            state[chat_id] = {"state": "idle"}

        # Start command resets the conversation
        if text == "/start":
            send_welcome(chat_id)
            state[chat_id] = {"state": "idle"}
            return

        # Admin command: only the configured admin user may access
        if text == "/admin" and user_id == ADMIN_ID_INT:
            show_admin_menu(chat_id)
            state[chat_id] = {"state": "admin_menu"}
            return

        # Check conversation state for this chat
        current_state = state.get(chat_id, {"state": "idle"}).get("state")

        if current_state == "awaiting_coin_quantity":
            # Expecting a number from the user
            platform = state[chat_id].get("platform")
            try:
                qty = float(text.replace(",", "."))
            except ValueError:
                send_message(chat_id, "Пожалуйста, введите количество цифрами (например, 300000).")
                return
            rate = data["coin_rates"].get(platform)
            if rate is None:
                send_message(chat_id, "Ошибка: неизвестная платформа.")
                state[chat_id] = {"state": "idle"}
                return
            total = (qty / 1_000_000) * rate
            # Round to two decimal places for display
            total_display = round(total, 2)
            state[chat_id].update({"qty": qty, "total": total_display})
            confirmation_keyboard = {
                "inline_keyboard": [
                    [{"text": "Оформить заказ", "callback_data": "confirm_order"}],
                ]
            }
            send_message(
                chat_id,
                f"Сумма: {total_display:.2f} руб. Количество: {qty:.0f} монет.\n"
                "Нажмите ‘Оформить заказ’, чтобы подтвердить.",
                reply_markup=confirmation_keyboard,
            )
            state[chat_id]["state"] = "awaiting_order_confirm"
            return

        if current_state == "admin_update_rate":
            # Expecting a new rate from the admin
            platform = state[chat_id].get("platform")
            try:
                new_rate = float(text.replace(",", "."))
            except ValueError:
                send_message(chat_id, "Введите корректное число для курса (рублей за 1 млн).")
                return
            data["coin_rates"][platform] = new_rate
            save_data(data)
            send_message(chat_id, f"Курс для {platform} обновлён: {new_rate:.2f} руб./млн.")
            state[chat_id] = {"state": "idle"}
            return

        # If no specific state is being awaited, prompt user to use menu
        send_message(chat_id, "Пожалуйста, используйте кнопки меню для выбора действия.")
        return

    # Callback queries from inline buttons
    if "callback_query" in update:
        query = update["callback_query"]
        callback_id = query["id"]
        chat_id = query["message"]["chat"]["id"]
        user_id = query["from"]["id"]
        data_cb = query["data"]

        # Ensure state entry exists
        if chat_id not in state:
            state[chat_id] = {"state": "idle"}

        # Handle main menu selections
        if data_cb == "buy_coins":
            send_platforms(chat_id)
            state[chat_id] = {"state": "select_platform"}
        elif data_cb == "buy_games":
            # Notify admin of a game request
            notification = (
                f"Поступил заказ на игру от пользователя id={user_id}. "
                f"Имя: @{query['from'].get('username', 'без имени')}"
            )
            send_message(ADMIN_ID_INT, notification)
            send_message(chat_id, "Заказ на игру отправлен. Скоро с вами свяжутся.")
            state[chat_id] = {"state": "idle"}
        elif data_cb == "buy_subscriptions":
            # Notify admin of a subscription request
            notification = (
                f"Поступил заказ на подписку от пользователя id={user_id}. "
                f"Имя: @{query['from'].get('username', 'без имени')}"
            )
            send_message(ADMIN_ID_INT, notification)
            send_message(chat_id, "Заказ на подписку отправлен. Скоро с вами свяжутся.")
            state[chat_id] = {"state": "idle"}
        elif data_cb.startswith("platform_"):
            # User picked a platform for coins
            _, platform = data_cb.split("_", 1)
            state[chat_id] = {"state": "awaiting_coin_quantity", "platform": platform}
            send_message(chat_id, f"Введите количество монет для {platform}:")
        elif data_cb == "confirm_order":
            # User confirmed a coin order
            order_state = state.get(chat_id, {})
            qty = order_state.get("qty")
            platform = order_state.get("platform")
            total = order_state.get("total")
            if qty is None or platform is None or total is None:
                send_message(chat_id, "Произошла ошибка при оформлении заказа. Попробуйте ещё раз.")
            else:
                send_message(
                    chat_id,
                    f"Заказ принят! {qty:.0f} монет для {platform}. Сумма: {total:.2f} руб.\n"
                    "Скоро с вами свяжутся для дальнейших инструкций."
                )
                # Notify admin
                notification = (
                    f"Новый заказ на монеты:\n"
                    f"Платформа: {platform}\n"
                    f"Количество: {qty:.0f}\n"
                    f"Сумма: {total:.2f} руб.\n"
                    f"От пользователя id={user_id}, имя: @{query['from'].get('username', 'без имени')}"
                )
                send_message(ADMIN_ID_INT, notification)
            state[chat_id] = {"state": "idle"}
        elif data_cb == "admin_show_rates":
            rates = data.get("coin_rates", {})
            lines = ["Текущие курсы (руб./млн монет):"]
            for plat, val in rates.items():
                lines.append(f"{plat}: {val:.2f}")
            send_message(chat_id, "\n".join(lines))
        elif data_cb == "admin_set_Xbox":
            state[chat_id] = {"state": "admin_update_rate", "platform": "Xbox"}
            send_message(chat_id, "Введите новый курс для Xbox (руб./млн):")
        elif data_cb == "admin_set_PlayStation":
            state[chat_id] = {"state": "admin_update_rate", "platform": "PlayStation"}
            send_message(chat_id, "Введите новый курс для PlayStation (руб./млн):")
        elif data_cb == "admin_set_PC":
            state[chat_id] = {"state": "admin_update_rate", "platform": "PC"}
            send_message(chat_id, "Введите новый курс для ПК (руб./млн):")
        elif data_cb == "admin_back":
            # Simply show the welcome message again
            send_welcome(chat_id)
            state[chat_id] = {"state": "idle"}
        # Unknown callback data – do nothing

        # Always answer callback queries to remove loading spinner
        answer_callback_query(callback_id)


def poll_loop() -> None:
    """Continuously poll the Telegram API for updates and handle them."""
    data = load_data()
    state: Dict[int, Dict[str, Any]] = {}
    offset: Optional[int] = None
    while True:
        params: Dict[str, Any] = {"timeout": 60}
        if offset is not None:
            params["offset"] = offset
        try:
            response = requests.get(
                f"https://api.telegram.org/bot{TOKEN}/getUpdates",
                params=params,
                timeout=65,
            )
            updates = response.json().get("result", [])
        except Exception:
            # If the network call fails, wait a bit and retry
            time.sleep(5)
            continue
        for update in updates:
            offset = update.get("update_id", 0) + 1
            handle_update(update, data, state)


def main() -> None:
    """Entry point when running the module as a script."""
    try:
        poll_loop()
    except KeyboardInterrupt:
        print("Bot stopped by user.")


if __name__ == "__main__":
    main()