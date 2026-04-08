import sys
import os
from dotenv import load_dotenv

# --- PATH BOOTSTRAP ---
# Ensure 'app' is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.sync.daily_export import export_daily_log, sync_to_drive

def run_historic_sync():
    print("--- 🚀 Starting One-Off HISTORIC Metrics Sync ---")
    
    # We use a large days_back to capture everything in the DB
    # (The script already handles deduplication)
    print("Step 1: Fetching all metrics from database and updating local CSV...")
    export_daily_log(days_back=730) # Back 2 years
    
    print("\nStep 2: Pushing the updated master file to Google Drive...")
    sync_to_drive()
    
    print("\n--- ✅ Historic Sync Complete ---")
    print("Note: Workouts were NOT exported in this one-off run.")

if __name__ == "__main__":
    run_historic_sync()
