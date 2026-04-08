import os
import sys
import logging
import asyncio
from datetime import date
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.constants import ParseMode

# Ensure 'app' is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import report functions and database utility
from app.decision_engine.llm import get_verbose_status, get_today_status 
from app.sync.main import sync_data
from app.sync.daily_export import export_daily_log, export_workouts, sync_to_drive
from app.sync.historic_sync import run_historic_sync
from app.db import get_cursor

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
        "/historicsync - Perform a one-off 2-year historic metrics sync\n"
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

async def force_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /sync command (Manual Sync & Drive Export)."""
    logging.info(f"🔄 Manual sync requested by {update.effective_user.first_name}")
    status_msg = await update.message.reply_text("🔄 Syncing data from Sparky and Intervals...")
    await update.message.chat.send_action(action="typing")
    
    import io
    from contextlib import redirect_stdout

    f = io.StringIO()
    try:
        with redirect_stdout(f):
            # 1. Update the local PostgreSQL database
            await asyncio.to_thread(sync_data)
            
            # 2. Generate the CSVs and push to Google Drive
            await asyncio.to_thread(export_daily_log)
            await asyncio.to_thread(export_workouts)
            await asyncio.to_thread(sync_to_drive)
        
        output = f.getvalue()
        # Truncate if too long for Telegram
        if len(output) > 3500:
            output = output[:3500] + "\n... (truncated)"
        
        await status_msg.edit_text(f"✅ **Sync Complete!**\n\n```\n{output}\n```", parse_mode='Markdown')
    except Exception as e:
        logging.error(f"⚠️ Sync Error: {e}")
        output = f.getvalue()
        await status_msg.edit_text(f"❌ **Sync Failed!**\n\nError: `{str(e)}` \n\nLog:\n```\n{output}\n```", parse_mode='Markdown')

async def force_historic_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /historicsync command (One-off Historic Export)."""
    logging.info(f"🚀 Historic sync requested by {update.effective_user.first_name}")
    status_msg = await update.message.reply_text("🚀 Starting historic sync (metrics only)...")
    await update.message.chat.send_action(action="typing")
    
    import io
    from contextlib import redirect_stdout

    f = io.StringIO()
    try:
        with redirect_stdout(f):
            # 1. Update the local PostgreSQL database (full sync first)
            await asyncio.to_thread(sync_data)
            
            # 2. Generate the historic CSV and push to Google Drive
            await asyncio.to_thread(run_historic_sync)
        
        output = f.getvalue()
        if len(output) > 3500:
            output = output[:3500] + "\n... (truncated)"
        
        await status_msg.edit_text(f"✅ **Historic Sync Complete!**\n\n```\n{output}\n```", parse_mode='Markdown')
    except Exception as e:
        logging.error(f"⚠️ Historic Sync Error: {e}")
        output = f.getvalue()
        await status_msg.edit_text(f"❌ **Historic Sync Failed!**\n\nError: `{str(e)}` \n\nLog:\n```\n{output}\n```", parse_mode='Markdown')

async def add_journal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log a journal entry via Telegram."""
    if not context.args:
        await update.message.reply_text("⚠️ Please provide your journal entry.\nUsage: `/journal Feeling strong today, managed the intervals well.`", parse_mode=ParseMode.MARKDOWN)
        return
    
    entry_text = " ".join(context.args)
    today_date = date.today()
    
    try:
        with get_cursor(dict_cursor=False) as cur:
            cur.execute("""
                INSERT INTO journal_entries (date, entry_text)
                VALUES (%s, %s)
            """, (today_date, entry_text))
            
        await update.message.reply_text("📓 **Journal entry saved for today!**", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to save entry: {str(e)}")

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
    application.add_handler(CommandHandler('historicsync', force_historic_sync))      
    application.add_handler(CommandHandler('journal', add_journal))
    application.run_polling()
