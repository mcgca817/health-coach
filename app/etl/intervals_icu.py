"""ETL for Intervals.icu data."""
import os
import sys
import requests
from datetime import datetime, timedelta

# Add parent directory to path so we can import db module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_cursor, log_job_start, log_job_success, log_job_failure
from dotenv import load_dotenv

load_dotenv('/opt/healthcoach/.env')

API_KEY = os.getenv('INTERVALS_API_KEY')
BASE_URL = 'https://intervals.icu/api/v1/athlete'

def fetch_wellness_data(days_back=7):
    """Fetch wellness data (HRV, RHR, weight, etc.) from Intervals.icu."""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back)
    url = f'{BASE_URL}/0/wellness'
    params = {
        'oldest': start_date.isoformat(),
        'newest': end_date.isoformat()
    }
    response = requests.get(url, auth=(API_KEY, ''), params=params)
    response.raise_for_status()
    return response.json()

def fetch_activities(days_back=7):
    """Fetch completed activities from Intervals.icu."""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back)
    url = f'{BASE_URL}/0/activities'
    params = {
        'oldest': start_date.isoformat(),
        'newest': end_date.isoformat()
    }
    response = requests.get(url, auth=(API_KEY, ''), params=params)
    response.raise_for_status()
    return response.json()

def import_wellness():
    """Import wellness data into database."""
    data = fetch_wellness_data(days_back=30) # Get last 30 days
    records = 0
    with get_cursor(dict_cursor=False) as cur:
        for record in data:
            # Extract date. In Intervals.icu, 'id' is the date
            date = record.get('id')
            if not date:
                continue
            
            # Extract fields (some might be null)
            weight = record.get('weight')
            hrv = record.get('hrv')
            rhr = record.get('restingHR')
            sleep_seconds = record.get('sleepSecs')
            sleep_hours = sleep_seconds / 3600 if sleep_seconds else None

            # Upsert into daily_biometrics
            cur.execute("""
                INSERT INTO daily_biometrics (date, weight_kg, hrv, rhr, sleep_hours)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (date) DO UPDATE SET
                    weight_kg = COALESCE(EXCLUDED.weight_kg, daily_biometrics.weight_kg),
                    hrv = COALESCE(EXCLUDED.hrv, daily_biometrics.hrv),
                    rhr = COALESCE(EXCLUDED.rhr, daily_biometrics.rhr),
                    sleep_hours = COALESCE(EXCLUDED.sleep_hours, daily_biometrics.sleep_hours)
            """, (date, weight, hrv, rhr, sleep_hours))
            records += 1
    return records

def import_training_load():
    """Import CTL/ATL/TSB data."""
    # Intervals.icu includes fitness metrics in the wellness endpoint
    data = fetch_wellness_data(days_back=30)
    records = 0
    with get_cursor(dict_cursor=False) as cur:
        for record in data:
            date = record.get('id')
            if not date:
                continue
            
            ctl = record.get('ctl')
            atl = record.get('atl')
            # Calculate TSB if we have CTL and ATL
            tsb = None
            if ctl is not None and atl is not None:
                tsb = ctl - atl
            
            if ctl or atl: # Only insert if we have at least one value
                cur.execute("""
                    INSERT INTO training_load (date, ctl, atl, tsb)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (date) DO UPDATE SET
                        ctl = COALESCE(EXCLUDED.ctl, training_load.ctl),
                        atl = COALESCE(EXCLUDED.atl, training_load.atl),
                        tsb = COALESCE(EXCLUDED.tsb, training_load.tsb),
                        updated_at = CURRENT_TIMESTAMP
                """, (date, ctl, atl, tsb))
                records += 1
    return records

def import_activities():
    """Import completed activities."""
    data = fetch_activities(days_back=7)
    records = 0
    with get_cursor(dict_cursor=False) as cur:
        for activity in data:
            # Extract fields
            external_id = activity.get('id')
            start_date = activity.get('start_date_local', '')[:10] # YYYY-MM-DD
            workout_type = activity.get('type', '').lower()
            duration_seconds = activity.get('moving_time') or activity.get('elapsed_time')
            duration_minutes = duration_seconds // 60 if duration_seconds else None
            tss = activity.get('icu_training_load')

            if not start_date or not external_id:
                continue

            cur.execute("""
                INSERT INTO workouts (
                    date, workout_type, completed, duration_minutes,
                    tss, external_id, completed_at
                )
                VALUES (%s, %s, true, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (external_id) DO UPDATE SET
                    completed = true,
                    duration_minutes = EXCLUDED.duration_minutes,
                    tss = EXCLUDED.tss,
                    completed_at = CURRENT_TIMESTAMP
            """, (start_date, workout_type, duration_minutes, tss, external_id))
            records += 1
    return records

def main():
    """Main ETL process."""
    job_name = 'etl_intervals_daily'
    run_id = log_job_start(job_name)
    try:
        print(f"Starting Intervals.icu ETL...")
        wellness_records = import_wellness()
        print(f"Imported {wellness_records} wellness records")
        
        load_records = import_training_load()
        print(f"Imported {load_records} training load records")
        
        activity_records = import_activities()
        print(f"Imported {activity_records} activities")
        
        total_records = wellness_records + load_records + activity_records
        log_job_success(run_id, total_records)
        print(f"ETL completed successfully. Total records: {total_records}")
    except Exception as e:
        error_msg = str(e)
        log_job_failure(run_id, error_msg)
        print(f"ETL failed: {error_msg}")
        sys.exit(1)

if __name__ == '__main__':
    main()
