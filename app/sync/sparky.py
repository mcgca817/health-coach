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
                    merged_bio[d_str] = {'date': row['entry_date'], 'weight_kg': None, 'steps': None, 'hrv_ms': None, 'sleep_hours': None}
                merged_bio[d_str]['weight_kg'] = row['weight']
                merged_bio[d_str]['steps'] = row['steps']

            # 2. Sleep & HRV
            cur.execute("""
                SELECT entry_date, avg_overnight_hrv, time_asleep_in_seconds
                FROM sleep_entries 
                WHERE entry_date >= CURRENT_DATE - %s::INTERVAL
                ORDER BY entry_date ASC
            """, (f"{days} days",))

            for row in cur.fetchall():
                d_str = str(row['entry_date'])
                if d_str not in merged_bio:
                    merged_bio[d_str] = {'date': row['entry_date'], 'weight_kg': None, 'steps': None, 'hrv_ms': None, 'sleep_hours': None}
                merged_bio[d_str]['hrv_ms'] = row['avg_overnight_hrv']
                if row['time_asleep_in_seconds']:
                    merged_bio[d_str]['sleep_hours'] = round(row['time_asleep_in_seconds'] / 3600.0, 2)

            # 3. Nutrition
            cur.execute("""
                SELECT 
                    entry_date, 
                    SUM(calories) as calories, 
                    SUM(protein) as protein, 
                    SUM(carbs) as carbs, 
                    SUM(fat) as fat
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
