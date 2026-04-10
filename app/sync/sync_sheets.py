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

# Read sheet IDs from environment variable (comma-separated string)
env_sheet_ids = os.getenv('GOOGLE_SHEET_IDS', "")
HEALTH_METRICS_IDS = [s.strip() for s in env_sheet_ids.split(",") if s.strip()]

def clean_kcal(val):
    """Strips ' kcal', commas, and units to return a clean float."""
    if not val or pd.isna(val):
        return 0.0
    numeric_part = re.sub(r"[^\d.]", "", str(val))
    try:
        return float(numeric_part)
    except ValueError:
        return 0.0

def clean_pct(val):
    """Strips '%' and returns a clean float."""
    if not val or pd.isna(val) or str(val).strip() == '':
        return None
    numeric_part = re.sub(r"[^\d.]", "", str(val))
    try:
        return float(numeric_part)
    except ValueError:
        return None

def parse_date(raw_date):
    """Normalizes the date string into a Python date object."""
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
    """Fetches a worksheet and returns a DataFrame with lowercase headers."""
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
    print("🚀 Starting Google Sheets Sync...")
    
    if not CREDS_FILE.exists():
        print(f"❌ ERROR: Credentials not found at {CREDS_FILE}")
        return

    try:
        gc = gspread.service_account(filename=str(CREDS_FILE))
        
        # Dictionary to hold merged data keyed by date
        # Format: { date_obj: {'kcal_burned': int, 'body_fat_pct': float} }
        merged_data = {}
        
        # Process each sheet ID
        for sheet_id in HEALTH_METRICS_IDS:
            try:
                sh = gc.open_by_key(sheet_id)
                print(f"✅ Opened Spreadsheet: {sh.title} (ID: {sheet_id})")
                
                # 1. Fetch Energy Data from 'Daily Metrics'
                print(f"  📂 Processing: [Daily Metrics] from {sh.title}")
                df_daily = fetch_sheet_data(sh, "Daily Metrics")
                if not df_daily.empty and 'date' in df_daily.columns:
                    for _, row in df_daily.iterrows():
                        d = parse_date(row.get('date'))
                        if not d: continue
                        
                        active = clean_kcal(row.get('active energy'))
                        resting = clean_kcal(row.get('resting energy'))
                        total_burn = int(active + resting) if (active > 0 or resting > 0) else None
                        
                        if d not in merged_data: merged_data[d] = {}
                        # Only update if we don't already have kcal_burned data for this date
                        if 'kcal_burned' not in merged_data[d] or merged_data[d]['kcal_burned'] is None:
                            merged_data[d]['kcal_burned'] = total_burn

                # 2. Fetch Body Fat from 'Weight'
                print(f"  📂 Processing: [Weight] from {sh.title}")
                df_weight = fetch_sheet_data(sh, "Weight")
                if not df_weight.empty and 'date' in df_weight.columns:
                    for _, row in df_weight.iterrows():
                        d = parse_date(row.get('date'))
                        if not d: continue
                        
                        bf_raw = row.get('fat')
                        bf_pct = clean_pct(bf_raw)
                        
                        if d not in merged_data: merged_data[d] = {}
                        # Only update if we don't already have body_fat_pct data for this date
                        if 'body_fat_pct' not in merged_data[d] or merged_data[d]['body_fat_pct'] is None:
                            merged_data[d]['body_fat_pct'] = bf_pct
                elif df_weight.empty:
                    print(f"  ⚠️ Skipping Weight processing from {sh.title} as sheet could not be loaded.")
                else:
                    print(f"  ⚠️ WARNING: Could not find a 'date' column in the Weight sheet from {sh.title}!")
                    
            except Exception as e:
                print(f"❌ Failed to access sheet {sheet_id}: {e}")
                continue

        # 3. Upsert into Database
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
    print("\n✨ Data synchronization complete.")
