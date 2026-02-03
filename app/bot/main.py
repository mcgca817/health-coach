"""
Main entry point for the Telegram Bot.
"""
import os
import sys
from telegram.ext import ApplicationBuilder, CommandHandler
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv('/opt/healthcoach/.env')

from bot.handlers import start, help_command, get_plan, status

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in .env")
        sys.exit(1)

    print("Starting Bot...")
    app = ApplicationBuilder().token(token).build()

    # Register Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("plan", get_plan))
    app.add_handler(CommandHandler("status", status))

    print("Bot is polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
