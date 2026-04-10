"""
Garmin Connect Integration.
Fetches daily wellness data (specifically Calorie Burn) directly from Garmin.
"""
import os
import logging
from datetime import date
from garminconnect import Garmin

def fetch_garmin_burn(target_date=None):
    """
    Connects to Garmin Connect and retrieves the total calories burned for a specific date.
    If no date is provided, defaults to today.
    """
    email = os.getenv('GARMIN_EMAIL')
    password = os.getenv('GARMIN_PASSWORD')
    
    if not email or not password:
        print("⚠️ Garmin credentials missing. Skipping direct Garmin sync.")
        return None

    if target_date is None:
        target_date = date.today()

    try:
        # Initialize Garmin client
        client = Garmin(email, password)
        client.login()
        
        # Fetch stats for the specific date
        stats = client.get_stats(target_date.isoformat())
        
        # Garmin provides totalCalories, activeCalories, and bmrCalories
        total_burn = stats.get('totalCalories')
        
        if total_burn:
            print(f"✅ Garmin: Retrieved {total_burn} kcal for {target_date}")
            return int(total_burn)
        
        return None

    except Exception as e:
        print(f"❌ Garmin Sync Error: {e}")
        return None
