"""
Main entry point for Data Sync.
Pulls from SparkyFitness & Intervals.icu -> Pushes to HealthCoach DB.
"""
import sys
import os
from dotenv import load_dotenv

# Force load the .env file
load_dotenv('/opt/healthcoach/.env')

# Add the parent directory (app/) to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_cursor, log_job_start, log_job_success, log_job_failure
from sync.sparky import fetch_recent_data
from sync.intervals import fetch_wellness_data

def sync_data():
    run_id = log_job_start("daily_sync")
    print("--- Starting Data Sync ---")
    
    try:
        # 1. Fetch Data
        sparky_data = fetch_recent_data(days=30)
        intervals_data = fetch_wellness_data(days=30)

        # 2. Write to Database
        with get_cursor() as cur:
            # --- A. Sync Biometrics (Sparky) ---
            for row in sparky_data['biometrics']:
                cur.execute("""
                    INSERT INTO daily_biometrics (date, weight_kg, steps)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (date) DO UPDATE SET
                        weight_kg = COALESCE(EXCLUDED.weight_kg, daily_biometrics.weight_kg),
                        steps = COALESCE(EXCLUDED.steps, daily_biometrics.steps)
                """, (row['date'], row['weight_kg'], row['steps']))

            # --- B. Sync Nutrition (Sparky) ---
            for row in sparky_data['nutrition']:
                cur.execute("""
                    INSERT INTO nutrition_actuals (date, kcal_actual, protein_actual_g, carbs_actual_g, fat_actual_g)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (date) DO UPDATE SET
                        kcal_actual = EXCLUDED.kcal_actual,
                        protein_actual_g = EXCLUDED.protein_actual_g,
                        carbs_actual_g = EXCLUDED.carbs_actual_g,
                        fat_actual_g = EXCLUDED.fat_actual_g
                """, (row['entry_date'], row['calories'], row['protein'], row['carbs'], row['fat']))

            # --- C. Sync Everything Else (Intervals) ---
            for row in intervals_data:
                cur.execute("""
                    INSERT INTO daily_biometrics 
                    (date, ctl, atl, tsb, resting_hr, hrv, kcal_burned, sleep_hours, weight_kg, steps)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (date) DO UPDATE SET
                        ctl = EXCLUDED.ctl,
                        atl = EXCLUDED.atl,
                        tsb = EXCLUDED.tsb,
                        resting_hr = COALESCE(EXCLUDED.resting_hr, daily_biometrics.resting_hr),
                        hrv = COALESCE(EXCLUDED.hrv, daily_biometrics.hrv),
                        kcal_burned = COALESCE(EXCLUDED.kcal_burned, daily_biometrics.kcal_burned),
                        sleep_hours = COALESCE(EXCLUDED.sleep_hours, daily_biometrics.sleep_hours),
                        weight_kg = COALESCE(EXCLUDED.weight_kg, daily_biometrics.weight_kg),
                        steps = COALESCE(EXCLUDED.steps, daily_biometrics.steps)
                """, (
                    row['date'], row['ctl'], row['atl'], row['tsb'], 
                    row['resting_hr'], row['hrv'], row['kcal_burned'], 
                    row['sleep_hours'], row['weight_kg'], row['steps']
                ))

        log_job_success(run_id, records_processed=len(intervals_data))
        print("--- Sync Complete ---")

    except Exception as e:
        log_job_failure(run_id, str(e))
        print(f"❌ Sync Failed: {e}")
        raise e

if __name__ == "__main__":
    sync_data()
