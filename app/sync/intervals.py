import os
import requests
from datetime import datetime, timedelta

def fetch_wellness_data(days=30):
    athlete_id = os.getenv('INTERVALS_ATHLETE_ID')
    api_key = os.getenv('INTERVALS_API_KEY')
    
    if not athlete_id or not api_key:
        print("⚠️  Intervals.icu credentials missing.")
        return []

    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    url = f"https://intervals.icu/api/v1/athlete/{athlete_id}/wellness?oldest={start_date}&newest={end_date}"
    
    try:
        response = requests.get(url, auth=('API_KEY', api_key))
        if response.status_code == 200:
            data = response.json()
            cleaned_data = []
            for day in data:
                # PERFORMANCE METRICS
                ctl = day.get('ctl') or 0
                atl = day.get('atl') or 0
                tsb = day.get('form') or (float(ctl) - float(atl))

                kcal_burned = day.get('kcal') or day.get('calories')
                sleep_secs = day.get('sleepSecs') or 0
                sleep_hrs = round(sleep_secs / 3600, 2) if sleep_secs > 0 else None
                
                # Extract body fat
                body_fat = day.get('bodyFat')

                cleaned_data.append({
                    'date': day.get('id'),
                    'ctl': round(float(ctl), 1),
                    'atl': round(float(atl), 1),
                    'tsb': round(float(tsb), 1),
                    'resting_hr': day.get('restingHR'),
                    'hrv': day.get('hrvSDNN') or day.get('hrv'),
                    'kcal_burned': int(kcal_burned) if kcal_burned else None,
                    'weight_kg': day.get('weight'),
                    'sleep_hours': sleep_hrs,
                    'steps': day.get('steps'),
                    'body_fat_pct': round(float(body_fat), 1) if body_fat is not None else None
                })            
            return cleaned_data
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def fetch_activities_data(days=30):
    athlete_id = os.getenv('INTERVALS_ATHLETE_ID')
    api_key = os.getenv('INTERVALS_API_KEY')
    
    url = f"https://intervals.icu/api/v1/athlete/{athlete_id}/activities"
    params = {"oldest": (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'), "newest": datetime.now().strftime('%Y-%m-%d')}
    
    try:
        response = requests.get(url, params=params, auth=('API_KEY', api_key))
        if response.status_code == 200:
            activities = response.json()
            cleaned = []
            for act in activities:
                cleaned.append({
                    'id': str(act.get('id')),
                    'date': act.get('start_date_local', '').split('T')[0],
                    'name': act.get('name', 'Unnamed'),
                    'type': act.get('type', 'Other'),
                    'distance_km': round((act.get('distance') or 0) / 1000, 2),
                    'moving_time_min': round((act.get('moving_time') or 0) / 60, 2),
                    'load': act.get('icu_training_load') or 0,
                    'average_watts': act.get('average_watts') or 0
                })
            return cleaned
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []
