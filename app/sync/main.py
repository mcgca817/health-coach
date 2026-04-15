"""
Main Data Synchronization Engine.
Orchestrates data retrieval from multiple providers (SparkyFitness, Intervals.icu, Google Sheets)
and performs atomic updates to the central PostgreSQL database.
"""
import sys
import os
from dotenv import load_dotenv

# --- CONFIGURATION & PATH SETUP ---
load_dotenv('/opt/healthcoach/.env')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_cursor, log_job_start, log_job_success, log_job_failure
from sync.sparky import fetch_recent_data, fetch_food_logs, fetch_calories_burned
from sync.intervals import fetch_wellness_data, fetch_activities_data
from sync.sync_sheets import sync_and_update

def setup_database(cur):
    """
    Bootstrap required helper tables and indexes.
    Ensures the application can recover if the primary schema is present but 
    supplementary tables are missing.
    """
    # Activities Table: Tracks individual workout sessions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id TEXT PRIMARY KEY,
            date DATE NOT NULL,
            name TEXT,
            type TEXT,
            distance_km NUMERIC(6,2),
            moving_time_min NUMERIC(6,2),
            load INTEGER,
            average_watts INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_activities_date ON activities(date DESC);
    """)

    # Granular Nutrition Logs: Detailed line-items from SparkyFitness
    cur.execute("""
        CREATE TABLE IF NOT EXISTS nutrition_logs (
            id SERIAL PRIMARY KEY,
            date DATE NOT NULL,
            logged_at TIMESTAMP,
            entry_text TEXT,
            kcal_actual INTEGER,
            protein_actual_g NUMERIC(5,1),
            carbs_actual_g NUMERIC(5,1),
            fat_actual_g NUMERIC(5,1),
            fibre_actual_g NUMERIC(5,1),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        -- Ensure logged_at exists if the table was created before this feature
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='nutrition_logs' AND column_name='logged_at') THEN
                ALTER TABLE nutrition_logs ADD COLUMN logged_at TIMESTAMP;
            END IF;
        END $$;
        CREATE INDEX IF NOT EXISTS idx_nut_logs_date ON nutrition_logs(date DESC);
    """)

def sync_data():
    """
    Core Sync Loop.
    1. Fetches data from all external APIs (Intervals & Sparky).
    2. Opens a single transaction to the database.
    3. Performs UPSERTs (Insert or Update on Conflict) for all records.
    4. Triggers secondary sync for Google Sheets.
    """
    run_id = log_job_start("daily_sync")
    print("--- Starting Data Sync ---")
    
    try:
        # --- 1. DATA ACQUISITION ---
        # Fetch 30 days of summary data and 7 days of granular logs
        sparky_data = fetch_recent_data(days=30)
        food_log_data = fetch_food_logs(days=7) 
        wellness_data = fetch_wellness_data(days=30)
        activities_data = fetch_activities_data(days=30)
        sparky_burn_data = fetch_calories_burned(days=30)

        print(f"--- Fetched Data Counts ---")
        print(f"Sparky Biometrics: {len(sparky_data.get('biometrics', []))}")
        print(f"Sparky Nutrition: {len(sparky_data.get('nutrition', []))}")
        print(f"Sparky Burn (Est): {len(sparky_burn_data)}")
        print(f"Intervals Wellness: {len(wellness_data)}")
        print(f"Intervals Activities: {len(activities_data)}")

        # --- 2. DATABASE PERSISTENCE ---
        with get_cursor() as cur:
            setup_database(cur)

            # A. Sync Sparky Burn Estimates (PRIMARY SOURCE for kcal_burned)
            for row in sparky_burn_data:
                cur.execute("""
                    INSERT INTO daily_biometrics (date, kcal_burned)
                    VALUES (%s, %s)
                    ON CONFLICT (date) DO UPDATE SET
                        kcal_burned = EXCLUDED.kcal_burned
                """, (row['date'], int(row['kcal_burned'])))

            # B. Sync Biometrics (Weight/Steps from Sparky)
            for row in sparky_data['biometrics']:
                cur.execute("""
                    INSERT INTO daily_biometrics (date, weight_kg, steps)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (date) DO UPDATE SET
                        weight_kg = COALESCE(EXCLUDED.weight_kg, daily_biometrics.weight_kg),
                        steps = COALESCE(EXCLUDED.steps, daily_biometrics.steps)
                """, (row['date'], row['weight_kg'], row['steps']))

            # C. Sync Nutrition Totals (Aggregated daily macros from Sparky)
            for row in sparky_data['nutrition']:
                cur.execute("""
                    INSERT INTO nutrition_actuals (date, kcal_actual, protein_actual_g, carbs_actual_g, fat_actual_g, fibre_actual_g)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (date) DO UPDATE SET
                        kcal_actual = EXCLUDED.kcal_actual,
                        protein_actual_g = EXCLUDED.protein_actual_g,
                        carbs_actual_g = EXCLUDED.carbs_actual_g,
                        fat_actual_g = EXCLUDED.fat_actual_g,
                        fibre_actual_g = EXCLUDED.fibre_actual_g
                """, (row['entry_date'], row['calories'], row['protein'], row['carbs'], row['fat'], row.get('fibre_actual_g', 0)))

            # D. Sync Granular Food Logs (Wipe and replace last 7 days to handle edits/deletions)
            cur.execute("DELETE FROM nutrition_logs WHERE date >= CURRENT_DATE - INTERVAL '7 days'")
            for row in food_log_data:
                name = row['food_name']
                brand = row['brand_name']
                entry_text = f"{name} ({brand})" if brand else name
                
                cur.execute("""
                    INSERT INTO nutrition_logs (date, logged_at, entry_text, kcal_actual, protein_actual_g, carbs_actual_g, fat_actual_g, fibre_actual_g)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (row['entry_date'], row['created_at'], entry_text, row['calories'], row['protein'], row['carbs'], row['fat'], row.get('fibre_actual_g', 0)))

            # E. Sync Wellness (Sleep, HRV, Performance Metrics from Intervals.icu)
            for row in wellness_data:
                # 1. Update Biometrics Table (Health metrics)
                # Note: We only update kcal_burned if Intervals actually provides it (> 0)
                cur.execute("""
                    INSERT INTO daily_biometrics 
                    (date, resting_hr, hrv, sleep_hours, weight_kg, steps, kcal_burned)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (date) DO UPDATE SET
                        resting_hr = COALESCE(EXCLUDED.resting_hr, daily_biometrics.resting_hr),
                        hrv = COALESCE(EXCLUDED.hrv, daily_biometrics.hrv),
                        sleep_hours = COALESCE(EXCLUDED.sleep_hours, daily_biometrics.sleep_hours),
                        weight_kg = COALESCE(EXCLUDED.weight_kg, daily_biometrics.weight_kg),
                        steps = COALESCE(EXCLUDED.steps, daily_biometrics.steps),
                        kcal_burned = CASE 
                            WHEN daily_biometrics.kcal_burned IS NULL OR daily_biometrics.kcal_burned = 0 THEN EXCLUDED.kcal_burned 
                            ELSE daily_biometrics.kcal_burned 
                        END
                """, (row['date'], row['resting_hr'], row['hrv'], 
                      row['sleep_hours'], row['weight_kg'], row['steps'], row['kcal_burned'] or 0))

                # 2. Update Training Load Table (Performance/Fitness metrics)
                cur.execute("""
                    INSERT INTO training_load (date, ctl, atl, tsb)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (date) DO UPDATE SET
                        ctl = EXCLUDED.ctl,
                        atl = EXCLUDED.atl,
                        tsb = EXCLUDED.tsb,
                        updated_at = CURRENT_TIMESTAMP
                """, (row['date'], row['ctl'], row['atl'], row['tsb']))

            # F. Sync Activities (Individual workout files/stats)
            for act in activities_data:
                cur.execute("""
                    INSERT INTO activities (id, date, name, type, distance_km, moving_time_min, load, average_watts)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        load = EXCLUDED.load,
                        average_watts = EXCLUDED.average_watts
                """, (act['id'], act['date'], act['name'], act['type'], 
                      act['distance_km'], act['moving_time_min'], act['load'], act['average_watts']))

        # --- 3. SECONDARY SYNC: GOOGLE SHEETS ---
        # Sheets sync handles additional metrics like manual 'Burn' data
        print("--- Triggering Google Sheets Sync ---")
        try:
            sync_and_update()
        except Exception as sheet_err:
            print(f"⚠️ Sheets Sync Warning: {sheet_err}")

        log_job_success(run_id, records_processed=len(wellness_data))
        print(f"--- Sync Complete: {len(wellness_data)} wellness, {len(activities_data)} activities, {len(food_log_data)} food entries ---")

    except Exception as e:
        log_job_failure(run_id, str(e))
        print(f"❌ Sync Failed: {e}")
        raise e

if __name__ == "__main__":
    sync_data()
