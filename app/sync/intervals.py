import os
import requests
from datetime import datetime, timedelta

def fetch_wellness_data(days=30):
    """
    Fetches wellness and training load data from Intervals.icu.
    Relies on HealthFit (iPhone) to push Apple Health data to Intervals first.
    """
    athlete_id = os.getenv('INTERVALS_ATHLETE_ID')
    api_key = os.getenv('INTERVALS_API_KEY')
    
    if not athlete_id or not api_key:
        print("⚠️  Intervals.icu credentials missing. Skipping.")
        return []

    # Calculate date range
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    url = f"https://intervals.icu/api/v1/athlete/{athlete_id}/wellness?oldest={start_date}&newest={end_date}"
    
    print(f"   - Fetching Intervals.icu data from {start_date} to {end_date}...")
    
    try:
        # Intervals.icu uses Basic Auth with 'API_KEY' as the username
        response = requests.get(url, auth=('API_KEY', api_key))
        
        if response.status_code == 200:
            data = response.json()
            cleaned_data = []
            
            for day in data:
                # 1. Capture Performance Metrics (CTL/ATL)
                ctl = day.get('ctl') or 0
                atl = day.get('atl') or 0
                
                # 2. TSB (Form) Calculation Fallback
                tsb = day.get('form')
                if tsb is None:
                    tsb = float(ctl) - float(atl)

                # 3. Total Daily Burn (TDEE) 
                # Prioritize 'kcal' (the HealthFit wellness field) over 'calories'
                kcal_burned = day.get('kcal') or day.get('calories')

                # 4. Sleep Calculation (Seconds to Hours)
                sleep_secs = day.get('sleepSecs')
                sleep_hrs = round(sleep_secs / 3600, 2) if sleep_secs else None

                cleaned_data.append({
                    'date': day.get('id'),
                    'ctl': round(float(ctl), 2),
                    'atl': round(float(atl), 2),
                    'tsb': round(float(tsb), 2),
                    'resting_hr': day.get('restingHR'),
                    'hrv': day.get('hrvSDNN') or day.get('hrv'),
                    'kcal_burned': int(kcal_burned) if kcal_burned else None,
                    'weight_kg': day.get('weight'),
                    'sleep_hours': sleep_hrs,
                    'steps': day.get('steps')
                })            
            print(f"   - Retrieved {len(cleaned_data)} days of training and wellness data.")
            return cleaned_data
        else:
            print(f"❌ Error fetching Intervals data: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Critical Error connecting to Intervals.icu: {e}")
        return []

if __name__ == "__main__":
    # For standalone testing
    from dotenv import load_dotenv
    load_dotenv('/opt/healthcoach/.env')
    test_data = fetch_wellness_data(7)
    for d in test_data:
        print(d)
