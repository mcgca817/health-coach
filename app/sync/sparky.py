import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv('/opt/healthcoach/.env')

def get_sparky_connection():
    conn = psycopg2.connect(
        host=os.getenv('SPARKY_HOST'),
        database=os.getenv('SPARKY_DB'),
        user=os.getenv('SPARKY_USER'),
        password=os.getenv('SPARKY_PASSWORD')
    )
    
    # --- RLS BYPASS ---
    user_id = os.getenv('SPARKY_USER_ID')
    if user_id:
        with conn.cursor() as cur:
            cur.execute("SET app.user_id = %s", (user_id,))
    
    return conn

def fetch_recent_data(days=30):
    """Fetches daily aggregated totals (Biometrics & Nutrition)."""
    conn = get_sparky_connection()
    data = {'biometrics': [], 'nutrition': []}
    
    merged_bio = {}

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            
            # 1. Weight & Steps
            cur.execute("""
                SELECT entry_date, weight, steps
                FROM check_in_measurements 
                WHERE entry_date >= CURRENT_DATE - %s::INTERVAL
                ORDER BY entry_date ASC
            """, (f"{days} days",))
            
            for row in cur.fetchall():
                d_str = str(row['entry_date'])
                if d_str not in merged_bio:
                    merged_bio[d_str] = {'date': row['entry_date'], 'weight_kg': None, 'steps': 0}
                
                if row['weight']: merged_bio[d_str]['weight_kg'] = float(row['weight'])
                if row['steps']: merged_bio[d_str]['steps'] = int(row['steps'])

            # 2. Nutrition Totals (Calculated from Quantity)
            # Fix: (quantity / serving_size) * calories
            cur.execute("""
                SELECT 
                    entry_date, 
                    SUM((quantity / NULLIF(serving_size, 0)) * calories) as calories, 
                    SUM((quantity / NULLIF(serving_size, 0)) * protein) as protein, 
                    SUM((quantity / NULLIF(serving_size, 0)) * carbs) as carbs, 
                    SUM((quantity / NULLIF(serving_size, 0)) * fat) as fat
                FROM food_entries
                WHERE entry_date >= CURRENT_DATE - %s::INTERVAL
                GROUP BY entry_date
                ORDER BY entry_date ASC
            """, (f"{days} days",))
            
            data['nutrition'] = cur.fetchall()
            
    finally:
        conn.close()

    data['biometrics'] = list(merged_bio.values())
    return data

def fetch_food_logs(days=7):
    """Fetches granular food entries with calculated macros."""
    conn = get_sparky_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Fix: Calculate actuals based on quantity eaten
            cur.execute("""
                SELECT 
                    entry_date, 
                    food_name,
                    brand_name, 
                    (quantity / NULLIF(serving_size, 0)) * calories as calories, 
                    (quantity / NULLIF(serving_size, 0)) * protein as protein,
                    (quantity / NULLIF(serving_size, 0)) * carbs as carbs,
                    (quantity / NULLIF(serving_size, 0)) * fat as fat
                FROM food_entries
                WHERE entry_date >= CURRENT_DATE - %s::INTERVAL
                ORDER BY entry_date DESC, created_at ASC
            """, (f"{days} days",))
            return cur.fetchall()
    finally:
        conn.close()
