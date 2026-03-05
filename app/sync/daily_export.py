import sys
import os
import base64
import requests
import subprocess
import pandas as pd
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# --- PATH BOOTSTRAP ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from google.oauth2 import service_account
from googleapiclient.discovery import build
from app.db import get_cursor

# --- CONFIG ---
RECIPIENT_EMAIL = "camwmcgregor@gmail.com" # <--- Put your Gmail here
CREDS_FILE = "/opt/healthcoach/config/google/service_account.json"
FIT_CSV_TOOL = "/opt/healthcoach/bin/FitCSVTool.jar"
EXPORT_DIR = "/opt/healthcoach/exports"

def send_email_with_attachments(file_paths):
    """Sends the daily CSVs as attachments via Gmail API."""
    try:
        # Note: Scopes must include gmail.send
        scopes = ['https://www.googleapis.com/auth/gmail.send']
        creds = service_account.Credentials.from_service_account_file(
            CREDS_FILE, scopes=scopes
        )
        
        # Build the Gmail service
        service = build('gmail', 'v1', credentials=creds)

        message = MIMEMultipart()
        message['to'] = RECIPIENT_EMAIL
        message['subject'] = f"🛡️ McPatty Performance Data: {date.today()}"
        
        body = "Attached are your daily performance metrics and workout CSVs for Gemini processing."
        message.attach(MIMEText(body, 'plain'))

        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue
                
            filename = os.path.basename(file_path)
            attachment = open(file_path, "rb")
            
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {filename}")
            message.attach(part)
            attachment.close()

        # Gmail API requires the message to be base64url encoded
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        
        print(f"✅ Email sent successfully to {RECIPIENT_EMAIL}")

    except Exception as e:
        print(f"❌ Email Error: {e}")

def export_daily_data():
    """Orchestrates the export and sends a single email with all files."""
    today = date.today()
    os.makedirs(EXPORT_DIR, exist_ok=True)
    files_to_send = []

    # 1. Export Daily Log (Biometrics + Nutrition)
    log_path = os.path.join(EXPORT_DIR, f"daily_metrics_{today}.csv")
    with get_cursor() as cur:
        cur.execute("""
            SELECT b.*, n.kcal_actual, n.protein_actual_g, n.carbs_actual_g, n.fat_actual_g, n.fibre_actual_g
            FROM daily_biometrics b
            LEFT JOIN nutrition_actuals n ON b.date = n.date
            WHERE b.date = %s
        """, (today,))
        row = cur.fetchone()
        if row:
            pd.DataFrame([dict(row)]).to_csv(log_path, index=False)
            files_to_send.append(log_path)

    # 2. Export Workouts
    api_key = os.getenv('INTERVALS_API_KEY')
    with get_cursor() as cur:
        cur.execute("SELECT id, name FROM activities WHERE date = %s", (today,))
        activities = cur.fetchall()

    for act in activities:
        url = f"https://intervals.icu/api/v1/activity/{act['id']}/file"
        r = requests.get(url, auth=('API_KEY', api_key))
        if r.status_code == 200:
            fit_path = os.path.join(EXPORT_DIR, f"{act['id']}.fit")
            csv_path = os.path.join(EXPORT_DIR, f"workout_{act['id']}.csv")
            
            with open(fit_path, 'wb') as f:
                f.write(r.content)
            
            try:
                subprocess.run(["java", "-jar", FIT_CSV_TOOL, "-b", fit_path, csv_path], check=True)
                files_to_send.append(csv_path)
            finally:
                if os.path.exists(fit_path): os.remove(fit_path)

    # 3. Send everything in one batch
    if files_to_send:
        send_email_with_attachments(files_to_send)
    else:
        print("⚠️ No data found to email today.")

if __name__ == "__main__":
    export_daily_data()
