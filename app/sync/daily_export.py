import sys
import os
import requests
import subprocess
import pandas as pd
from datetime import date
from dotenv import load_dotenv
load_dotenv('/opt/healthcoach/.env')

# --- PATH BOOTSTRAP ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.db import get_cursor

# --- CONFIG ---
EXPORT_DIR = "/opt/healthcoach/exports"
FIT_CSV_TOOL = "/opt/healthcoach/bin/FitCSVTool.jar"
REMOTE_PATH = os.getenv('GDRIVE_REMOTE_PATH', 'gdrive:Operation Outlive')
MASTER_FILE_NAME = "daily_metrics_master.csv"

def export_daily_log():
    """Appends today's metrics to the master CSV checkpoint."""
    today = date.today()
    master_path = os.path.join(EXPORT_DIR, MASTER_FILE_NAME)
    
    with get_cursor() as cur:
        cur.execute("""
            SELECT b.*, n.kcal_actual, n.protein_actual_g, n.carbs_actual_g, n.fat_actual_g, n.fibre_actual_g
            FROM daily_biometrics b
            LEFT JOIN nutrition_actuals n ON b.date = n.date
            WHERE b.date = %s
        """, (today,))
        row = cur.fetchone()
        
        if row:
            new_data = pd.DataFrame([dict(row)])
            
            # If master exists, append; otherwise create new
            if os.path.exists(master_path):
                master_df = pd.read_csv(master_path)
                # Avoid duplicate rows for the same date if script is re-run
                master_df = master_df[master_df['date'] != str(today)]
                updated_df = pd.concat([master_df, new_data], ignore_index=True)
                updated_df.to_csv(master_path, index=False)
                print(f"✅ Updated {MASTER_FILE_NAME} with data for {today}")
            else:
                new_data.to_csv(master_path, index=False)
                print(f"✅ Created new master checkpoint: {MASTER_FILE_NAME}")
        else:
            print(f"⚠️ No metrics found in database for {today}")

def export_workouts():
    """Downloads and converts today's FIT files."""
    today = date.today()
    api_key = os.getenv('INTERVALS_API_KEY')
    
    with get_cursor() as cur:
        cur.execute("SELECT id, name FROM activities WHERE date = %s", (today,))
        activities = cur.fetchall()

    for act in activities:
        url = f"https://intervals.icu/api/v1/activity/{act['id']}/file"
        r = requests.get(url, auth=('API_KEY', api_key))
        
        if r.status_code == 200:
            fit_path = os.path.join(EXPORT_DIR, f"{act['id']}.fit")
            csv_path = os.path.join(EXPORT_DIR, f"workout_{act['id']}.csv")
            
            with open(fit_path, 'wb') as f:
                f.write(r.content)
            
            try:
                subprocess.run(["java", "-jar", FIT_CSV_TOOL, "-b", fit_path, csv_path], check=True)
                print(f"✅ Workout {act['id']} converted.")
            finally:
                if os.path.exists(fit_path): 
                    os.remove(fit_path)

def sync_to_drive():
    """Syncs the local directory to Google Drive."""
    print("🔄 Syncing to Google Drive...")
    try:
        # rclone copy ensures the master file is overwritten with the latest version
        subprocess.run(["rclone", "copy", EXPORT_DIR, REMOTE_PATH], check=True)
        print("✅ Sync successful.")
    except Exception as e:
        print(f"❌ Sync failed: {e}")

if __name__ == "__main__":
    os.makedirs(EXPORT_DIR, exist_ok=True)
    export_daily_log()
    export_workouts()
    sync_to_drive()
