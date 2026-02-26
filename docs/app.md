# `app` package

Purpose: contains the runtime services that interact with users and external systems.

Key modules
- `app/bot/` — Telegram bot implementation.
  - `main.py` - Bot entrypoint. Exposes `/start`, `/status`, and `/today` commands.
  - `handlers.py` - Command handlers and message formatting.
- `app/sync/` — Data synchronization helpers.
  - `sync_sheets.py`, `intervals.py`, `sparky.py` - connectors to external APIs and sheet-sync logic.
- `app/db.py` — Database connection utilities and run-history helpers.

Run notes
- The bot reads environment variables from `/opt/healthcoach/.env` by default. Ensure `TELEGRAM_BOT_TOKEN` and Postgres credentials are present.
- Run the bot with:

```bash
python -m app.bot.main
```

Testing and development
- Use a virtual environment and install `app/requirements.txt`.
- The bot uses `python-telegram-bot` and `dotenv` (see `app/requirements.txt`).
