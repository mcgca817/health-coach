"""
Context builder for the Decision Engine.
Collects data from DB to form the 'state' for the LLM.
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path to import db
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_cursor

def get_recent_biometrics(days=7):
    """Fetch biometrics for the last N days."""
    with get_cursor() as cur:
        cur.execute("""
            SELECT date, weight_kg, hrv, rhr, sleep_hours, steps
            FROM daily_biometrics
            WHERE date >= CURRENT_DATE - %s::INTERVAL
            ORDER BY date DESC
        """, (f"{days} days",))
        return cur.fetchall()

def get_current_load():
    """Fetch the latest fitness metrics (CTL, ATL, TSB)."""
    with get_cursor() as cur:
        cur.execute("""
            SELECT ctl, atl, tsb
            FROM training_load
            ORDER BY date DESC
            LIMIT 1
        """)
        return cur.fetchone()

def get_recent_nutrition(days=7):
    """Fetch nutrition actuals for the last N days."""
    with get_cursor() as cur:
        cur.execute("""
            SELECT date, kcal_actual, protein_actual_g, carbs_actual_g, fat_actual_g
            FROM nutrition_actuals
            WHERE date >= CURRENT_DATE - %s::INTERVAL
            ORDER BY date DESC
        """, (f"{days} days",))
        return cur.fetchall()

def get_system_phase():
    """Get the current active phase (e.g., 'recomp', 'race_prep')."""
    with get_cursor() as cur:
        cur.execute("""
            SELECT phase, start_date, end_date
            FROM system_phase
            WHERE active = true
            ORDER BY start_date DESC
            LIMIT 1
        """)
        return cur.fetchone()

def get_rules():
    """Fetch all safety rules and thresholds."""
    with get_cursor() as cur:
        cur.execute("SELECT rule_name, rule_value, rule_unit FROM rule_config")
        rules = {}
        for row in cur.fetchall():
            rules[row['rule_name']] = row['rule_value']
        return rules

def build_context():
    """Aggregate all data into a single dictionary."""
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "biometrics": get_recent_biometrics(),
        "load": get_current_load(),
        "nutrition": get_recent_nutrition(),
        "phase": get_system_phase(),
        "rules": get_rules()
    }
