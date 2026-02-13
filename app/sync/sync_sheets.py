import os
import sys
import re
import gspread
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Ensure we can find 'app' by looking two levels up from this script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.db import get_cursor
load_dotenv('/opt/healthcoach/.env')

# --- CONFIGURATION ---
BASE_DIR = Path("/opt/healthcoach")
CREDS_FILE = BASE_DIR / "config" / "google" / "service_account.json"
HEALTH_METRICS_ID = "1SCsxip1B9zm8fV-QybWCdceyj-H1K4yzTH0spdi4Ekw"

def clean_kcal(val):
    """Strips ' kcal', commas, and units to return a clean float."""
    if not val or pd.isna(val):
        return 0.0
    # Use regex to keep only digits and decimal points
    numeric_part = re.sub(r"[^\d.]", "", str(val))
    try:
        return float(numeric_part)
    except ValueError:
        return 0.0

def update_database(df):
    """Parses the DataFrame and upserts calculated TDEE into Postgres."""
    with get_cursor() as cur:
        count = 0
        for _, row in df.iterrows():
            try:
                raw_date = str(row.get('Date', '')).strip()
                if not raw_date or raw_date == 'Date': continue
                
                # 1. Parse NZ Date Format (DD/MM/YYYY) for Postgres compatibility
                try:
                    clean_date = datetime.strptime(raw_date, "%d/%m/%Y").date()
                except ValueError:
                    # Fallback for ISO or other formats
                    clean_date = pd.to_datetime(raw_date).date()

                # 2. Extract and Sum Active + Resting Energy
                active = clean_kcal(row.get('Active Energy'))
                resting = clean_kcal(row.get('Resting Energy'))
                total_burn = int(active + resting)

                if total_burn <= 0: continue

                # 3. UPSERT into daily_biometrics
                cur.execute("""
                    INSERT INTO daily_biometrics (date, kcal_burned)
                    VALUES (%s, %s)
                    ON CONFLICT (date) DO UPDATE 
                    SET kcal_burned = EXCLUDED.kcal_burned
                """, (clean_date, total_burn))
                count += 1
                
            except Exception as e:
                print(f"      ⚠️ Row Error for {raw_date}: {e}")
        
        print(f"    ✅ Successfully upserted {count} rows.")

def sync_and_update():
    print("🚀 Starting Google Sheets Sync...")
    
    if not CREDS_FILE.exists():
        print(f"❌ ERROR: Credentials not found at {CREDS_FILE}")
        return

    try:
        gc = gspread.service_account(filename=str(CREDS_FILE))
        sh = gc.open_by_key(HEALTH_METRICS_ID)
        print(f"✅ Opened Spreadsheet: {sh.title}")
        
        # We specifically target the 'Daily Metrics' tab
        try:
            worksheet = sh.worksheet("Daily Metrics")
            print(f"  📂 Processing: [Daily Metrics]")
            
            all_values = worksheet.get_all_values()
            if not all_values:
                print("  ⚠️ Worksheet is empty.")
                return
            
            # Use first row as headers and create DataFrame
            headers = [h.strip() for h in all_values[0]]
            df = pd.DataFrame(all_values[1:], columns=headers)
            
            update_database(df)
            
        except gspread.exceptions.WorksheetNotFound:
            print("❌ ERROR: 'Daily Metrics' tab not found in the spreadsheet.")
                
    except Exception as e:
        print(f"❌ Sync Failed: {e}")

if __name__ == "__main__":
    sync_and_update()
    print("\n✨ Data synchronization complete.")
