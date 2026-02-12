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

def get_recent_biometrics(days=14):
    """Fetch biometrics (Weight, HRV, Sleep) + Training Load (CTL, ATL) for context."""
    with get_cursor() as cur:
        # We fetch 14 days so the LLM can see the trend
        cur.execute("""
            SELECT 
                date, 
                weight_kg, 
                hrv, 
                resting_hr, 
                sleep_hours, 
                steps,
                ctl,
                atl,
                tsb
            FROM daily_biometrics
            WHERE date >= CURRENT_DATE - %s::INTERVAL
            ORDER BY date DESC
        """, (f"{days} days",))
        
        # Convert rows to a list of dictionaries
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in cur.fetchall()]
        return results

def get_recent_nutrition(days=7):
    """Fetch nutrition actuals for the last N days."""
    with get_cursor() as cur:
        cur.execute("""
            SELECT date, kcal_actual, protein_actual_g, carbs_actual_g, fat_actual_g
            FROM nutrition_actuals
            WHERE date >= CURRENT_DATE - %s::INTERVAL
            ORDER BY date DESC
        """, (f"{days} days",))
        
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]

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
        row = cur.fetchone()
        if row:
            return dict(zip([desc[0] for desc in cur.description], row))
        return {"phase": "maintenance", "start_date": str(datetime.now().date())}

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
    biometrics = get_recent_biometrics()
    
    # Extract the most recent load data specifically for easy access
    current_load = {}
    if biometrics:
        latest = biometrics[0]
        current_load = {
            "ctl": latest.get('ctl'),
            "atl": latest.get('atl'),
            "tsb": latest.get('tsb')
        }

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "biometrics": biometrics,
        "load": current_load, # Explicitly passing current load summary
        "nutrition": get_recent_nutrition(),
        "phase": get_system_phase(),
        "rules": get_rules()
    }
