
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Path setup for internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load env before importing our modules
if os.path.exists('/app/app'): # Container path
    load_dotenv('/opt/healthcoach/.env')
elif os.path.exists('/opt/healthcoach/.env'):
    load_dotenv('/opt/healthcoach/.env')
else:
    load_dotenv()

from app.db import get_cursor
from app.sync.sparky import fetch_calories_burned

def backfill_sparky_burn(days=90):
    """
    Backfills kcal_burned from Sparky into daily_biometrics for the specified window.
    """
    print(f"--- 🚀 Starting {days}-Day kcal_burned Backfill from Sparky ---")
    
    try:
        # 1. Fetch data from Sparky using our new formula
        print(f"Fetching last {days} days from SparkyFitness DB...")
        burn_data = fetch_calories_burned(days=days)
        print(f"Fetched {len(burn_data)} records.")
        
        # 2. Update local database
        with get_cursor() as cur:
            count = 0
            for row in burn_data:
                # We overwrite kcal_burned because Sparky is now our source of truth
                cur.execute("""
                    INSERT INTO daily_biometrics (date, kcal_burned)
                    VALUES (%s, %s)
                    ON CONFLICT (date) DO UPDATE SET
                        kcal_burned = EXCLUDED.kcal_burned
                """, (row['date'], int(row['kcal_burned'])))
                count += 1
            
            print(f"✅ Successfully updated {count} rows in daily_biometrics.")
            
    except Exception as e:
        print(f"❌ Backfill Failed: {e}")

if __name__ == "__main__":
    # If a window is passed as arg, use it; otherwise default to 90 days
    window = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    backfill_sparky_burn(window)
