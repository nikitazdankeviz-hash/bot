# Zdankevich Store Telegram Bot

This repository contains a lightweight Telegram bot to assist customers in purchasing in‑game coins, games and subscriptions for various gaming platforms. The bot greets users immediately, presents simple menu options and automatically notifies the store owner (administrator) of any incoming orders.

## Features

* **Instant greeting** – as soon as a user starts the bot they receive a welcome message explaining how the store works.
* **Clear menu navigation** – users can buy coins, games or subscriptions via inline buttons. When buying coins they first select their gaming platform (Xbox, PlayStation or PC) and then enter the quantity of coins.
* **Automatic price calculation** – the bot computes the total price based on configurable exchange rates (rubles per million coins) and asks the user to confirm the purchase.
* **Admin notifications** – whenever a user orders a game, subscription or confirms a coin purchase, the bot automatically sends a private message to the administrator containing the order details.
* **Admin panel** – the administrator can use the `/admin` command to view or adjust coin exchange rates directly through a simple menu.

## Setup

Before running the bot you need to set two environment variables:

* `TELEGRAM_BOT_TOKEN` – the token provided by BotFather when you created your bot.
* `TELEGRAM_ADMIN_ID` – your own Telegram user ID. You can find your user ID using various Telegram bots such as `@userinfobot`.

### Installing dependencies

This project uses the `requests` library to communicate with the Telegram Bot API. Install it with pip:

```bash
pip install requests
```

Alternatively, install all dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Running the bot

Once the environment variables are set and dependencies installed, run:

```bash
python bot.py
```

The script uses long polling to fetch updates from Telegram. For production use you might consider running the bot as a system service or behind a process supervisor such as `systemd`.

### Changing coin rates

As the administrator you can adjust the price per million coins via the admin panel. Send the `/admin` command to the bot from your personal account and choose the appropriate option. The new rates are stored in `data.json` within the bot’s directory.

## Files

* `bot.py` – main script implementing the bot logic.
* `data.json` – JSON file storing exchange rates for coins. Created automatically on first run.
* `requirements.txt` – list of Python dependencies.

## License

This project is provided without any warranties. You are free to use and modify the code for your own needs.