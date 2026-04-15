"""
SparkyFitness Database Integration.
Connects to the external SparkyFitness PostgreSQL instance to retrieve 
biometrics (Weight/Steps) and detailed nutrition logs.
"""
import os
import psycopg2
import pytz
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# --- TIMEZONE CONFIGURATION ---
LOCAL_TZ = pytz.timezone('Pacific/Auckland')

# Load environment variables
if os.path.exists('/opt/healthcoach/.env'):
    load_dotenv('/opt/healthcoach/.env')
else:
    load_dotenv()

def get_sparky_connection():
    """
    Establish a connection to the SparkyFitness external DB.
    Uses app.user_id session variable to bypass RLS (Row Level Security) 
    and fetch data for the configured athlete only.
    """
    conn = psycopg2.connect(
        host=os.getenv('SPARKY_HOST'),
        database=os.getenv('SPARKY_DB'),
        user=os.getenv('SPARKY_USER'),
        password=os.getenv('SPARKY_PASSWORD')
    )
    
    # --- RLS BYPASS ---
    # Set the session user ID so Sparky's security policies allow our queries
    user_id = os.getenv('SPARKY_USER_ID')
    if user_id:
        with conn.cursor() as cur:
            cur.execute("SET app.user_id = %s", (user_id,))
    
    return conn

def fetch_recent_data(days=30):
    """
    Retrieves aggregated daily summary data (Weight, Steps, and Macro Totals).
    """
    conn = get_sparky_connection()
    data = {'biometrics': [], 'nutrition': []}
    merged_bio = {}

    # Use tomorrow's local date for the upper bound to catch any TZ overlap 
    # where Sparky entries might be logged with a timestamp that UTC sees as future
    local_tomorrow = (datetime.now(LOCAL_TZ) + timedelta(days=1)).date()

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            
            # 1. Fetch Weight & Steps from the check-in table
            cur.execute("""
                SELECT entry_date, weight, steps
                FROM check_in_measurements 
                WHERE entry_date >= %s::DATE - %s::INTERVAL AND entry_date <= %s::DATE
                ORDER BY entry_date ASC
            """, (local_tomorrow, f"{days} days", local_tomorrow))
            
            for row in cur.fetchall():
                d_str = str(row['entry_date'])
                if d_str not in merged_bio:
                    merged_bio[d_str] = {'date': row['entry_date'], 'weight_kg': None, 'steps': 0}
                
                if row['weight']: merged_bio[d_str]['weight_kg'] = float(row['weight'])
                if row['steps']: merged_bio[d_str]['steps'] = int(row['steps'])

            # 2. Fetch Aggregated Nutrition Totals
            # Macros are calculated by multiplying quantity eaten by the serving-size ratio.
            cur.execute("""
                SELECT 
                    entry_date, 
                    SUM((quantity / NULLIF(serving_size, 0)) * calories) as calories, 
                    SUM((quantity / NULLIF(serving_size, 0)) * protein) as protein, 
                    SUM((quantity / NULLIF(serving_size, 0)) * carbs) as carbs, 
                    SUM((quantity / NULLIF(serving_size, 0)) * fat) as fat,
                    SUM((quantity / NULLIF(serving_size, 0)) * dietary_fiber) as fibre_actual_g
                FROM food_entries
                WHERE entry_date >= %s::DATE - %s::INTERVAL AND entry_date <= %s::DATE
                GROUP BY entry_date::date
                ORDER BY entry_date::date ASC
            """, (local_tomorrow, f"{days} days", local_tomorrow))
            
            data['nutrition'] = cur.fetchall()
            
    finally:
        conn.close()

    data['biometrics'] = list(merged_bio.values())
    return data

def fetch_calories_burned(days=30):
    """
    Calculates estimated calories burned using Sparky's exercise logs and step data.
    Formula: SUM(calories_burned) + (steps * 0.0233)
    """
    conn = get_sparky_connection()
    user_id = os.getenv('SPARKY_USER_ID')
    local_tomorrow = (datetime.now(LOCAL_TZ) + timedelta(days=1)).date()
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Join from measurements to ensure we get a row for every day with steps
            # even if no formal exercise was logged.
            cur.execute("""
                SELECT 
                    m.entry_date as date,
                    COALESCE(SUM(e.calories_burned), 0) + COALESCE(m.steps * 0.0233, 0) + 2080 AS kcal_burned
                FROM check_in_measurements m
                LEFT JOIN exercise_entries e 
                    ON m.entry_date = e.entry_date 
                    AND m.user_id = e.user_id
                WHERE m.user_id = %s
                  AND m.entry_date >= %s::DATE - %s::INTERVAL 
                  AND m.entry_date <= %s::DATE
                GROUP BY m.entry_date, m.steps
                ORDER BY m.entry_date DESC
            """, (user_id, local_tomorrow, f"{days} days", local_tomorrow))
            
            return cur.fetchall()
    finally:
        conn.close()

def fetch_food_logs(days=7):
    """
    Retrieves individual food entry details for the last N days.
    Used for the /today granular breakdown.
    """
    conn = get_sparky_connection()
    local_tomorrow = (datetime.now(LOCAL_TZ) + timedelta(days=1)).date()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    entry_date, 
                    created_at,
                    food_name,
                    brand_name, 
                    (quantity / NULLIF(serving_size, 0)) * calories as calories, 
                    (quantity / NULLIF(serving_size, 0)) * protein as protein,
                    (quantity / NULLIF(serving_size, 0)) * carbs as carbs,
                    (quantity / NULLIF(serving_size, 0)) * fat as fat,
                    (quantity / NULLIF(serving_size, 0)) * dietary_fiber as fibre_actual_g
                FROM food_entries
                WHERE entry_date >= %s::DATE - %s::INTERVAL AND entry_date <= %s::DATE
                ORDER BY entry_date DESC, created_at ASC
            """, (local_tomorrow, f"{days} days", local_tomorrow))
            return cur.fetchall()
    finally:
        conn.close()
