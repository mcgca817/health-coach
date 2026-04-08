"""
Telegram command handlers.
"""
import sys
import os
import json
from telegram import Update
from telegram.constants import ParseMode
from datetime import date
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
    """Check the health of the system and latest biometrics."""
    try:
        with get_cursor() as cur:
            # Check DB connection
            cur.execute("SELECT 1")
            
            # Fetch latest Biometrics (Weight + Training Load)
            cur.execute("""
                SELECT date, weight_kg, ctl, atl, tsb 
                FROM daily_biometrics 
                ORDER BY date DESC 
                LIMIT 1
            """)
            bio = cur.fetchone()
            
            # Check active phase
            cur.execute("SELECT phase FROM system_phase WHERE active = true")
            phase_row = cur.fetchone()
            current_phase = phase_row['phase'] if phase_row else "Unknown"

            if bio:
                date = bio['date']
                weight = bio['weight_kg'] or "N/A"
                ctl = bio['ctl'] or "N/A"
                atl = bio['atl'] or "N/A"
                tsb = bio['tsb'] or "N/A"
                
                msg = (
                    f"✅ **System Status: Online**\n\n"
                    f"📅 **Date:** `{date}`\n"
                    f"🌊 **Phase:** `{current_phase}`\n\n"
                    f"⚖️ **Weight:** `{weight} kg`\n"
                    f"🚴 **Fitness (CTL):** `{ctl}`\n"
                    f"🔋 **Fatigue (ATL):** `{atl}`\n"
                    f"📉 **Form (TSB):** `{tsb}`"
                )
            else:
                msg = "✅ **System Online**, but no biometrics found."

            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await update.message.reply_text(f"❌ System Error: {str(e)}")

#from app.decision_engine.llm import get_coaching_advice

#async def coach_command(update, context):
#    """Handler for the /coach command"""
#    # Send an initial 'thinking' message
#    status_msg = await update.message.reply_text("📋 McPatty Coach is reviewing your biometrics...")
#    
#    try:
#        # Get the tactical briefing
#        advice = get_coaching_advice()
#        
#        # Update the message with the actual advice
#        await status_msg.edit_text(advice, parse_mode='Markdown')
#        
#    except Exception as e:
#        await status_msg.edit_text(f"❌ Coach hit a technical snag: {str(e)}")


# Add the new handler function
async def add_journal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log a journal entry via Telegram."""
    if not context.args:
        await update.message.reply_text("⚠️ Please provide your journal entry.\nUsage: `/journal Feeling strong today, managed the intervals well.`", parse_mode=ParseMode.MARKDOWN)
        return
    
    entry_text = " ".join(context.args)
    today = date.today()
    
    try:
        # dict_cursor=False because we aren't fetching rows
        with get_cursor(dict_cursor=False) as cur:
            cur.execute("""
                INSERT INTO journal_entries (date, entry_text)
                VALUES (%s, %s)
            """, (today, entry_text))
            
        await update.message.reply_text("📓 **Journal entry saved for today!**", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to save entry: {str(e)}")
