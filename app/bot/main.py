import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# Ensure 'app' is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import BOTH report functions
from app.decision_engine.llm import get_verbose_status, get_today_status 
from app.sync.main import sync_data
from app.sync.daily_export import export_daily_log, export_workouts, sync_to_drive
from app.bot.handlers import add_journal

# Load environment variables
load_dotenv('/opt/healthcoach/.env')
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    welcome_text = (
        "📊 *McPatty Performance Coach Active*\n\n"
        "Commands:\n"
        "/today - Quick snapshot of today's nutrition & training\n"
        "/status - Full 30-day performance report\n"
        "/sync - Force a manual data synchronization\n"
        "/journal <text> - Add a brief journal entry for today\n"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /status command (Full Report)."""
    logging.info(f"📡 Status requested by {update.effective_user.first_name}")
    status_msg = await update.message.reply_text("🔄 Syncing full history...")
    await update.message.chat.send_action(action="typing")
    
    try:
        await asyncio.to_thread(sync_data)
        report = await asyncio.to_thread(get_verbose_status)
        await status_msg.delete()
        
        if len(report) > 4000:
            for x in range(0, len(report), 4000):
                await update.message.reply_text(report[x:x+4000], parse_mode='Markdown')
        else:
            await update.message.reply_text(report, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"⚠️ Status Error: {e}")
        await status_msg.edit_text(f"❌ Error: {str(e)}")

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /today command (Quick Snapshot)."""
    logging.info(f"⚡ Today requested by {update.effective_user.first_name}")
    status_msg = await update.message.reply_text("🔄 Syncing today's data...")
    await update.message.chat.send_action(action="typing")
    
    try:
        # 1. Sync Data (Fast check)
        await asyncio.to_thread(sync_data)
        
        # 2. Get Today's Summary
        report = await asyncio.to_thread(get_today_status)
        
        # 3. Send
        await status_msg.delete()
        await update.message.reply_text(report, parse_mode='Markdown')

    except Exception as e:
        logging.error(f"⚠️ Today Error: {e}")
        await status_msg.edit_text(f"❌ Error: {str(e)}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    welcome_text = (
        "📊 *McPatty Performance Coach Active*\n\n"
        "Commands:\n"
        "/today - Quick snapshot of today's nutrition & training\n"
        "/status - Full 30-day performance report\n"
        "/sync - Force a manual data synchronization\n" # <-- Add this line
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def force_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /sync command (Manual Sync & Drive Export)."""
    logging.info(f"🔄 Manual sync requested by {update.effective_user.first_name}")
    status_msg = await update.message.reply_text("🔄 Syncing data from Sparky and Intervals...")
    await update.message.chat.send_action(action="typing")
    
    try:
        # 1. Update the local PostgreSQL database
        await asyncio.to_thread(sync_data)
        await status_msg.edit_text("✅ Database updated. Generating export for Google Drive...")
        
        # 2. Generate the CSVs and push to Google Drive
        await asyncio.to_thread(export_daily_log)
        await asyncio.to_thread(export_workouts)
        await asyncio.to_thread(sync_to_drive)
        
        await status_msg.edit_text("✅ Sync complete! Database and Google Drive are fully up to date.")
    except Exception as e:
        logging.error(f"⚠️ Sync Error: {e}")
        await status_msg.edit_text(f"❌ Sync failed: {str(e)}")

if __name__ == "__main__":
    if not API_TOKEN:
        logging.error("❌ TELEGRAM_BOT_TOKEN not found.")
        sys.exit(1)

    logging.info("🚀 McPatty Bot starting...")
    
    application = ApplicationBuilder().token(API_TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('status', status))
    application.add_handler(CommandHandler('today', today)) 
    application.add_handler(CommandHandler('sync', force_sync))      
    application.add_handler(CommandHandler('journal', add_journal))
    application.run_polling()

