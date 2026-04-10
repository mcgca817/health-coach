import sys
import os
from dotenv import load_dotenv

# Path setup
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_cursor
from sync.intervals import fetch_wellness_data, fetch_activities_data

def backfill(days=180):
    print(f"--- 🚀 Starting {days}-day Backfill from Intervals.icu ---")
    wellness = fetch_wellness_data(days=days)
    activities = fetch_activities_data(days=days)
    print(f"Fetched {len(wellness)} wellness records and {len(activities)} activities.")

    with get_cursor() as cur:
        # 1. Biometrics & Training Load
        for r in wellness:
            cur.execute("""
                INSERT INTO daily_biometrics (date, hrv, resting_hr, sleep_hours, weight_kg, steps)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (date) DO UPDATE SET
                    hrv = EXCLUDED.hrv,
                    resting_hr = EXCLUDED.resting_hr,
                    sleep_hours = EXCLUDED.sleep_hours,
                    weight_kg = EXCLUDED.weight_kg,
                    steps = EXCLUDED.steps
            """, (r["date"], r["hrv"], r["resting_hr"], r["sleep_hours"], r["weight_kg"], r["steps"]))

            cur.execute("""
                INSERT INTO training_load (date, ctl, atl, tsb)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (date) DO UPDATE SET
                    ctl = EXCLUDED.ctl,
                    atl = EXCLUDED.atl,
                    tsb = EXCLUDED.tsb
            """, (r["date"], r["ctl"], r["atl"], r["tsb"]))

        # 2. Activities
        for a in activities:
            cur.execute("""
                INSERT INTO activities (id, date, name, type, distance_km, moving_time_min, load, average_watts)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (a["id"], a["date"], a["name"], a["type"], a["distance_km"], a["moving_time_min"], a["load"], a["average_watts"]))

    print("--- ✅ Backfill Complete ---")

if __name__ == "__main__":
    backfill()
