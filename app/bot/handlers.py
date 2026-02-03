"""
Telegram command handlers.
"""
import sys
import os
import json
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_cursor

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message."""
    await update.message.reply_text(
        "👋 **Health Coach Online**\n\n"
        "Commands:\n"
        "/plan - View today's plan\n"
        "/status - Check system status\n"
        "/help - Show this menu",
        parse_mode=ParseMode.MARKDOWN
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help menu."""
    await start(update, context)

async def get_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch the latest generated plan from the DB."""
    try:
        with get_cursor() as cur:
            # Get the most recent plan (created today or yesterday)
            cur.execute("""
                SELECT plan_json, llm_reasoning, date
                FROM plans_daily
                ORDER BY date DESC
                LIMIT 1
            """)
            row = cur.fetchone()
            
            if not row:
                await update.message.reply_text("⚠️ No plan found for today.")
                return

            plan = row['plan_json']
            reasoning = row['llm_reasoning']
            date = row['date']

            # Format the output nicely
            nut = plan.get('nutrition', {})
            training = plan.get('training', {})

            msg = (
                f"📅 **Plan for {date}**\n\n"
                f"🍽️ **Nutrition**\n"
                f"• Calories: `{nut.get('kcal', 0)}`\n"
                f"• Protein: `{nut.get('protein', 0)}g`\n"
                f"• Carbs: `{nut.get('carbs', 0)}g`\n"
                f"• Fat: `{nut.get('fat', 0)}g`\n"
                f"• Refeed: `{'Yes' if nut.get('refeed') else 'No'}`\n\n"
                f"🏋️ **Training**\n"
                f"• Type: {training.get('workout_type', 'Rest')}\n"
                f"• Duration: {training.get('duration_minutes', 0)} mins\n"
                f"• Intensity: {training.get('intensity_zone', 'N/A')}\n"
                f"_{training.get('description', '')}_\n\n"
                f"🧠 **Reasoning**\n"
                f"{reasoning}"
            )
            
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await update.message.reply_text(f"Error fetching plan: {str(e)}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check the health of the system."""
    try:
        with get_cursor() as cur:
            # Check DB connection
            cur.execute("SELECT 1")
            
            # Check latest biometrics date
            cur.execute("SELECT date FROM daily_biometrics ORDER BY date DESC LIMIT 1")
            bio = cur.fetchone()
            last_bio = bio['date'] if bio else "None"
            
            # Check active phase
            cur.execute("SELECT phase FROM system_phase WHERE active = true")
            phase = cur.fetchone()
            current_phase = phase['phase'] if phase else "None"

            msg = (
                "✅ **System Status: Online**\n\n"
                f"• **Active Phase:** `{current_phase}`\n"
                f"• **Last Biometrics:** `{last_bio}`\n"
                f"• **Database:** Connected"
            )
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await update.message.reply_text(f"❌ System Error: {str(e)}")
