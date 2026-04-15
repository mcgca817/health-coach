"""
Google Sheets Data Integration.
Fetches manual metrics (Active Burn, Body Fat %) from specific Google Sheets
using a Google Service Account.
"""
import os
import sys
import re
import gspread
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Path setup for internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.db import get_cursor
load_dotenv('/opt/healthcoach/.env')

# --- CONFIGURATION ---
# Use /app prefix for containerized environment, fallback to /opt/healthcoach for legacy
BASE_DIR = Path("/app") if os.path.exists("/app/app") else Path("/opt/healthcoach")
CREDS_FILE = BASE_DIR / "config" / "google" / "service_account.json"

# Read sheet IDs from environment variable (comma-separated string in .env)
env_sheet_ids = os.getenv('GOOGLE_SHEET_IDS', "")
HEALTH_METRICS_IDS = [s.strip() for s in env_sheet_ids.split(",") if s.strip()]

def clean_kcal(val):
    """Normalizes calorie strings into floats (handles commas and units)."""
    if not val or pd.isna(val):
        return 0.0
    numeric_part = re.sub(r"[^\d.]", "", str(val))
    try:
        return float(numeric_part)
    except ValueError:
        return 0.0

def clean_pct(val):
    """Normalizes percentage strings into floats."""
    if not val or pd.isna(val) or str(val).strip() == '':
        return None
    numeric_part = re.sub(r"[^\d.]", "", str(val))
    try:
        return float(numeric_part)
    except ValueError:
        return None

def parse_date(raw_date):
    """Attempts to parse diverse date formats into a standard Python date object."""
    raw_date = str(raw_date).strip()
    if not raw_date or raw_date.lower() == 'date': 
        return None
    try:
        return datetime.strptime(raw_date, "%d/%m/%Y").date()
    except ValueError:
        try:
            return pd.to_datetime(raw_date).date()
        except Exception:
            return None

def fetch_sheet_data(sh, sheet_name):
    """Reads a worksheet tab and returns it as a DataFrame with lowercase headers."""
    try:
        worksheet = sh.worksheet(sheet_name)
        all_values = worksheet.get_all_values()
        if not all_values:
            return pd.DataFrame()
        
        headers = [str(h).strip().lower() for h in all_values[0]]
        df = pd.DataFrame(all_values[1:], columns=headers)
        return df
    except gspread.exceptions.WorksheetNotFound:
        print(f"  ❌ ERROR: '{sheet_name}' tab not found.")
        return pd.DataFrame()
    except Exception as e:
        print(f"  ❌ ERROR reading '{sheet_name}': {e}")
        return pd.DataFrame()

def sync_and_update():
    """
    Main Orchestrator for Google Sheets Sync.
    1. Iterates through all configured Spreadsheet IDs.
    2. Parses 'Daily Metrics' tab for Energy Burn.
    3. Parses 'Weight' tab for Body Fat Percentage.
    4. Upserts all found data into daily_biometrics.
    """
    print("🚀 Starting Google Sheets Sync...")
    
    if not CREDS_FILE.exists():
        print(f"❌ ERROR: Google Service Account Credentials not found at {CREDS_FILE}")
        return

    try:
        # Authenticate using the Service Account JSON key
        gc = gspread.service_account(filename=str(CREDS_FILE))
        
        # Format: { date_obj: {'kcal_burned': int, 'body_fat_pct': float} }
        merged_data = {}
        
        for sheet_id in HEALTH_METRICS_IDS:
            try:
                sh = gc.open_by_key(sheet_id)
                print(f"✅ Opened Spreadsheet: {sh.title}")
                
                # 1. Fetch Body Fat Data (from 'Weight' tab)
                df_weight = fetch_sheet_data(sh, "Weight")
                if not df_weight.empty and 'date' in df_weight.columns:
                    for _, row in df_weight.iterrows():
                        d = parse_date(row.get('date'))
                        if not d: continue
                        
                        bf_raw = row.get('fat')
                        bf_pct = clean_pct(bf_raw)
                        
                        if d not in merged_data: merged_data[d] = {}
                        if 'body_fat_pct' not in merged_data[d] or merged_data[d]['body_fat_pct'] is None:
                            merged_data[d]['body_fat_pct'] = bf_pct
                    
            except Exception as e:
                print(f"❌ Failed to access sheet {sheet_id}: {e}")
                continue

        # 3. Database Persistence
        with get_cursor() as cur:
            count = 0
            bf_count = 0
            
            for sync_date, metrics in merged_data.items():
                kcal_burned = metrics.get('kcal_burned')
                body_fat_pct = metrics.get('body_fat_pct')
                
                if kcal_burned is None and body_fat_pct is None:
                    continue
                    
                if body_fat_pct is not None:
                    bf_count += 1
                
                try:
                    cur.execute("""
                        INSERT INTO daily_biometrics (date, kcal_burned, body_fat_pct)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (date) DO UPDATE 
                        SET 
                            kcal_burned = COALESCE(EXCLUDED.kcal_burned, daily_biometrics.kcal_burned),
                            body_fat_pct = COALESCE(EXCLUDED.body_fat_pct, daily_biometrics.body_fat_pct)
                    """, (sync_date, kcal_burned, body_fat_pct))
                    count += 1
                except Exception as e:
                    print(f"      ⚠️ Database Error for {sync_date}: {e}")
            
            print(f"    ✅ Successfully upserted {count} rows. (Found Body Fat in {bf_count} rows)")
                
    except Exception as e:
        print(f"❌ Sync Failed: {e}")

if __name__ == "__main__":
    sync_and_update()
