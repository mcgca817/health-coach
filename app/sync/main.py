"""
Main entry point for Data Sync.
Pulls from SparkyFitness & Intervals.icu -> Pushes to HealthCoach DB.
"""
import sys
import os
from dotenv import load_dotenv
# Force load the .env file
load_dotenv('/opt/healthcoach/.env')


# Add the parent directory (app/) to sys.path so we can import 'db'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_cursor
from sync.sparky import fetch_recent_data

# Try importing intervals, handle gracefully if the file isn't there yet
try:
    from sync.intervals import fetch_wellness_data
except ImportError:
    print("⚠️  Warning: app/sync/intervals.py not found. Skipping Intervals sync.")
    def fetch_wellness_data(days=30): return []

def sync_data():
    print("--- Starting Data Sync ---")
    
    # 1. Fetch Sparky Data
    print("Fetching data from SparkyFitness...")
    try:
        sparky_data = fetch_recent_data(days=30)
    except Exception as e:
        print(f"FAILED to connect to Sparky: {e}")
        sparky_data = {}

    # 2. Fetch Intervals Data
    print("Fetching data from Intervals.icu...")
    try:
        intervals_data = fetch_wellness_data(days=30)
    except Exception as e:
        print(f"FAILED to connect to Intervals: {e}")
        intervals_data = []

    # 3. Write to Database
    with get_cursor() as cur:
        
        # --- A. Sync Sparky Biometrics ---
        count_bio = 0
        for row in sparky_data.get('biometrics', []):
            cur.execute("""
                INSERT INTO daily_biometrics 
                (date, weight_kg, hrv, sleep_hours, steps)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (date) DO UPDATE SET
                    weight_kg = COALESCE(EXCLUDED.weight_kg, daily_biometrics.weight_kg),
                    hrv = COALESCE(EXCLUDED.hrv, daily_biometrics.hrv),
                    sleep_hours = COALESCE(EXCLUDED.sleep_hours, daily_biometrics.sleep_hours),
                    steps = COALESCE(EXCLUDED.steps, daily_biometrics.steps)
            """, (
                row['date'], row['weight_kg'], row['hrv_ms'], 
                row['sleep_hours'], row['steps']
            ))
            count_bio += 1
            
        # --- B. Sync Sparky Nutrition ---
        count_nut = 0
        for row in sparky_data.get('nutrition', []):
            cur.execute("""
                INSERT INTO nutrition_actuals
                (date, kcal_actual, protein_actual_g, carbs_actual_g, fat_actual_g)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (date) DO UPDATE SET
                    kcal_actual = EXCLUDED.kcal_actual,
                    protein_actual_g = EXCLUDED.protein_actual_g,
                    carbs_actual_g = EXCLUDED.carbs_actual_g,
                    fat_actual_g = EXCLUDED.fat_actual_g
            """, (
                row['entry_date'], row['calories'], row['protein'], 
                row['carbs'], row['fat']
            ))
            count_nut += 1

        # --- C. Sync Intervals Training Load ---
        count_intervals = 0
        if intervals_data:
            for row in intervals_data:
                cur.execute("""
                    INSERT INTO daily_biometrics 
                    (date, ctl, atl, tsb, resting_hr, hrv, kcal_burned)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (date) DO UPDATE SET
                        ctl = EXCLUDED.ctl,
                        atl = EXCLUDED.atl,
                        tsb = EXCLUDED.tsb,
                        resting_hr = COALESCE(EXCLUDED.resting_hr, daily_biometrics.resting_hr),
                        hrv = COALESCE(EXCLUDED.hrv, daily_biometrics.hrv),
                        kcal_burned = COALESCE(EXCLUDED.kcal_burned, daily_biometrics.kcal_burned)
                """, (
                    row['date'], row['ctl'], row['atl'], row['tsb'], 
                    row['resting_hr'], row['hrv'], row['kcal_burned']
                ))
                count_intervals += 1

        print(f"Synced {count_bio} biometric records (Sparky).")
        print(f"Synced {count_nut} nutrition records (Sparky).")
        print(f"Synced {count_intervals} training load records (Intervals).")

if __name__ == "__main__":
    sync_data()
