"""
Main entry point for Data Sync.
Pulls from SparkyFitness -> Pushes to HealthCoach DB.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_cursor
from sync.sparky import fetch_recent_data

def sync_data():
    print("--- Starting Data Sync ---")
    
    print("Fetching data from SparkyFitness...")
    try:
        data = fetch_recent_data(days=30)
    except Exception as e:
        print(f"FAILED to connect to Sparky: {e}")
        return

    with get_cursor() as cur:
        # Sync Biometrics
        count_bio = 0
        for row in data.get('biometrics', []):
            # We use COALESCE(EXCLUDED.col, daily_biometrics.col)
            # This ensures that if the new data is None, we keep the old data.
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
            
        # Sync Nutrition
        count_nut = 0
        for row in data.get('nutrition', []):
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

        print(f"Synced {count_bio} biometric records.")
        print(f"Synced {count_nut} nutrition records.")

if __name__ == "__main__":
    sync_data()
