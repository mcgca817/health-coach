import os
import requests
import base64
from datetime import datetime, timedelta

def get_auth_header():
    api_key = os.getenv('INTERVALS_API_KEY')
    # Intervals.icu uses Basic Auth with username='API_KEY' and password='development'
    token = base64.b64encode(f"API_KEY:{api_key}".encode('utf-8')).decode('utf-8')
    return {'Authorization': f'Basic {token}'}

def fetch_wellness_data(days=30):
    athlete_id = os.getenv('INTERVALS_ATHLETE_ID')
    if not athlete_id or not os.getenv('INTERVALS_API_KEY'):
        print("⚠️ Intervals.icu credentials missing. Skipping.")
        return []

    # Calculate date range
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    url = f"https://intervals.icu/api/v1/athlete/{athlete_id}/wellness?oldest={start_date}&newest={end_date}"
    
    print(f"   - Fetching Intervals.icu data from {start_date} to {end_date}...")
    
    try:
        # Note: Username is 'API_KEY', password is usually ignored or 'development'
        response = requests.get(url, auth=('API_KEY', os.getenv('INTERVALS_API_KEY')))
        
        if response.status_code == 200:
            data = response.json()
            cleaned_data = []
            
            for day in data:
                # We only care about the metrics relevant to the Health Coach
                cleaned_data.append({
                    'date': day.get('id'),
                    'ctl': day.get('ctl'),
                    'atl': day.get('atl'),
                    'tsb': day.get('form'),
                    'resting_hr': day.get('restingHR'),
                    'hrv': day.get('hrvSDNN') or day.get('hrv'),
                    'kcal_burned': day.get('calories') # Total energy expenditure from Intervals
                })            
            print(f"   - Retrieved {len(cleaned_data)} days of training load data.")
            return cleaned_data
        else:
            print(f"❌ Error fetching Intervals data: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Critical Error connecting to Intervals.icu: {e}")
        return []

if __name__ == "__main__":
    # Test run
    from dotenv import load_dotenv
    load_dotenv() # Load local .env if running manually
    data = fetch_wellness_data(7)
    for d in data:
        print(d)
