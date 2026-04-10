"""
Garmin Connect Integration with Session Persistence.
Fetches daily wellness data (specifically Calorie Burn) directly from Garmin.
Supports MFA by saving a session token after the first manual login.
"""
import os
import logging
import json
from datetime import date
from dotenv import load_dotenv
from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)

# Token file location
SESSION_FILE = "/opt/healthcoach/logs/garmin_session.json"

# Load environment variables
load_dotenv('/opt/healthcoach/.env')

def fetch_garmin_burn(target_date=None):
    """
    Connects to Garmin Connect and retrieves the total calories burned for a specific date.
    Uses a saved session file to bypass MFA on subsequent runs.
    """
    email = os.getenv('GARMIN_EMAIL')
    password = os.getenv('GARMIN_PASSWORD')
    
    if not email or not password:
        print("⚠️ Garmin credentials missing. Skipping direct Garmin sync.")
        return None

    if target_date is None:
        target_date = date.today()

    try:
        # 1. Initialize Garmin client
        client = Garmin(email, password)
        
        # 2. Try to load an existing session
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r") as f:
                saved_session = json.load(f)
                # Apply the session to the client
                client.display_name = saved_session.get("display_name")
                client.session_data = saved_session.get("session_data")
                print("🔄 Garmin: Using existing session token.")
        
        # 3. Login (will use session if valid, otherwise will try to login)
        # Note: If MFA is required and session is invalid, this will fail in background.
        client.login()
        
        # 4. Save the current session for next time
        session_to_save = {
            "display_name": client.display_name,
            "session_data": client.session_data
        }
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        with open(SESSION_FILE, "w") as f:
            json.dump(session_to_save, f)

        # 5. Fetch stats
        stats = client.get_stats(target_date.isoformat())
        total_burn = stats.get('totalCalories')
        
        if total_burn:
            print(f"✅ Garmin: Retrieved {total_burn} kcal for {target_date}")
            return int(total_burn)
        
        return None

    except GarminConnectAuthenticationError:
        print("❌ Garmin Auth Error: Login failed. If you have MFA, run this script manually once on the server.")
        return None
    except Exception as e:
        print(f"❌ Garmin Sync Error: {e}")
        return None

if __name__ == "__main__":
    # If run directly, this allows the user to handle the interactive MFA prompt
    print("🚀 Garmin Manual Session Initialization")
    burn = fetch_garmin_burn()
    if burn:
        print(f"✨ Success! Current burn is {burn} kcal. Session saved to {SESSION_FILE}")
    else:
        print("🚨 Sync failed. Check credentials or MFA input.")
