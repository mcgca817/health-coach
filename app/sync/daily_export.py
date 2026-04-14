"""
Daily CSV Export Engine.
Processes database records into flattened CSV files for external analysis.
- Handles workout conversion from .FIT to .CSV using Garmin's FitCSVTool.
- Synchronizes local files to Google Drive via rclone.
"""
import sys
import os
import requests
import subprocess
import pandas as pd
from datetime import date, timedelta
from dotenv import load_dotenv

# Load environment variables
if os.path.exists('/opt/healthcoach/.env'):
    load_dotenv('/opt/healthcoach/.env')
else:
    load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.db import get_cursor

# --- CONFIGURATION ---
# Use /app prefix for containerized environment, fallback to /opt/healthcoach for legacy
BASE_PATH = "/app" if os.path.exists("/app/app") else "/opt/healthcoach"
EXPORT_DIR = os.path.join(BASE_PATH, "exports")
FIT_CSV_TOOL = os.path.join(BASE_PATH, "bin", "FitCSVTool.jar")
REMOTE_PATH = os.getenv('GDRIVE_REMOTE_PATH', 'gdrive:Operation Outlive')
MASTER_FILE_NAME = "daily_metrics_master.csv"

def export_daily_log(days_back=30):
    """
    Exports a unified metrics table to a master CSV file.
    - Uses FULL OUTER JOIN to capture all dates from all source tables.
    - Implements deduplication to ensure the file can grow without duplicates.
    """
    start_date = date.today() - timedelta(days=days_back)
    master_path = os.path.join(EXPORT_DIR, MASTER_FILE_NAME)
    
    print(f"--- Exporting Metrics (since {start_date}) ---")
    
    with get_cursor() as cur:
        # Unified query joining Biometrics, Nutrition, and Training Load
        cur.execute("""
            SELECT 
                COALESCE(b.date, n.date, t.date) as date,
                b.weight_kg, b.body_fat_pct, b.sleep_hours, b.hrv, 
                b.resting_hr, b.steps,
                t.ctl, t.atl, t.tsb, b.kcal_burned,
                n.kcal_actual, n.protein_actual_g, n.carbs_actual_g, n.fat_actual_g, n.fibre_actual_g
            FROM daily_biometrics b
            FULL OUTER JOIN nutrition_actuals n ON b.date = n.date
            FULL OUTER JOIN training_load t ON COALESCE(b.date, n.date) = t.date
            WHERE COALESCE(b.date, n.date, t.date) >= %s
            ORDER BY date ASC
        """, (start_date,))
        rows = cur.fetchall()
        
        if not rows:
            print(f"⚠️ No metrics found in database since {start_date}")
            return

        new_data = pd.DataFrame([dict(row) for row in rows])
        new_data['date'] = new_data['date'].astype(str)
        
        if os.path.exists(master_path):
            try:
                master_df = pd.read_csv(master_path)
                master_df['date'] = master_df['date'].astype(str)
                
                # Deduplication: Remove dates we are about to re-insert
                dates_to_update = new_data['date'].unique()
                master_df = master_df[~master_df['date'].isin(dates_to_update)]
                
                # Merge, sort, and save
                updated_df = pd.concat([master_df, new_data], ignore_index=True)
                updated_df = updated_df.sort_values('date')
                
                updated_df.to_csv(master_path, index=False)
                print(f"✅ Updated {MASTER_FILE_NAME} with {len(new_data)} days of data.")
            except Exception as e:
                print(f"❌ Error updating master CSV: {e}. Recreating...")
                new_data.to_csv(master_path, index=False)
        else:
            new_data.to_csv(master_path, index=False)
            print(f"✅ Created new master checkpoint: {MASTER_FILE_NAME}")

def export_workouts(days_back=7):
    """
    Downloads individual workout files (.FIT) from Intervals.icu and converts them to .CSV.
    Only processes workouts that haven't been exported yet.
    """
    start_date = date.today() - timedelta(days=days_back)
    api_key = os.getenv('INTERVALS_API_KEY')
    
    if not api_key:
        print("⚠️ INTERVALS_API_KEY missing. Skipping workout export.")
        return

    print(f"--- Exporting Workouts (last {days_back} days) ---")
    
    with get_cursor() as cur:
        cur.execute("SELECT id, name, date FROM activities WHERE date >= %s", (start_date,))
        activities = cur.fetchall()

    for act in activities:
        csv_path = os.path.join(EXPORT_DIR, f"workout_{act['id']}.csv")
        
        # Avoid redundant work
        if os.path.exists(csv_path):
            continue
            
        print(f"🔄 Processing workout: {act['name']} ({act['date']})")
        url = f"https://intervals.icu/api/v1/activity/{act['id']}/file"
        r = requests.get(url, auth=('API_KEY', api_key))
        
        if r.status_code == 200:
            fit_path = os.path.join(EXPORT_DIR, f"{act['id']}.fit")
            
            with open(fit_path, 'wb') as f:
                f.write(r.content)
            
            try:
                # Convert binary FIT to readable CSV
                if os.path.exists(FIT_CSV_TOOL):
                    subprocess.run(["java", "-jar", FIT_CSV_TOOL, "-b", fit_path, csv_path], check=True)
                    print(f"   ✅ Converted to CSV.")
                else:
                    print(f"   ⚠️ FitCSVTool.jar not found at {FIT_CSV_TOOL}")
            except Exception as e:
                print(f"   ❌ Conversion failed for {act['id']}: {e}")
            finally:
                # Cleanup binary fit file to save space
                if os.path.exists(fit_path): 
                    os.remove(fit_path)
        else:
            print(f"   ⚠️ Failed to download FIT file for {act['id']} (Status: {r.status_code})")

def sync_to_drive():
    """
    Uses rclone to mirror the local exports directory to a Google Drive folder.
    - REMOTE_PATH is defined in group_vars (e.g., 'gdrive:Operation Outlive').
    """
    print("🔄 Syncing to Google Drive...")
    if not REMOTE_PATH:
        print("⚠️ GDRIVE_REMOTE_PATH not set. Skipping drive sync.")
        return
        
    try:
        # rclone copy is non-destructive (adds/updates files but doesn't delete)
        result = subprocess.run(
            ["rclone", "copy", EXPORT_DIR, REMOTE_PATH], 
            capture_output=True, 
            text=True, 
            check=True
        )
        print("✅ Drive sync successful.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Drive sync failed: {e}")
        if e.stderr:
            print(f"   Error details: {e.stderr.strip()}")
    except Exception as e:
        print(f"❌ Unexpected error during sync: {e}")

if __name__ == "__main__":
    os.makedirs(EXPORT_DIR, exist_ok=True)
    export_daily_log(days_back=30)
    export_workouts(days_back=7)
    sync_to_drive()
