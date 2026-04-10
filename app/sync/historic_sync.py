"""
Historic Data Sync Utility.
Provides a one-off mechanism to backfill metrics into the master CSV file.
Designed to be triggered via the Telegram bot or manually on the server.
"""
import sys
import os
from dotenv import load_dotenv

# --- PATH BOOTSTRAP ---
# Ensure the root 'app' module is discoverable for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.sync.daily_export import export_daily_log, sync_to_drive

def run_historic_sync():
    """
    Triggers a wide-window export of metrics only.
    - Captures the last 2 years of data from the database.
    - Updates the master CSV and pushes to Google Drive.
    - Workouts are excluded to maintain speed.
    """
    print("--- 🚀 Starting One-Off HISTORIC Metrics Sync ---")
    
    # We use a 730-day window to ensure all historical DB records are captured.
    # The export logic handles deduplication automatically.
    print("Step 1: Fetching all metrics from database and updating local CSV...")
    export_daily_log(days_back=730) 
    
    print("\nStep 2: Pushing the updated master file to Google Drive...")
    sync_to_drive()
    
    print("\n--- ✅ Historic Sync Complete ---")
    print("Note: Workout FIT files were NOT processed in this run.")

if __name__ == "__main__":
    run_historic_sync()
