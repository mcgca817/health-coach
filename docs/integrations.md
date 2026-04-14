# 🔌 API Integrations

McPatty Performance Coach integrates with several third-party platforms to build a 360-degree view of an athlete's health.

## 🚵 Intervals.icu (v1 API)
*   **Purpose**: Source of truth for training load and wellness.
*   **Authentication**: Basic Auth using `INTERVALS_API_KEY` and `INTERVALS_ATHLETE_ID`.
*   **Data Points**:
    *   **Wellness**: CTL, ATL, Form, Sleep Hours, HRV (SDNN), Resting HR.
    *   **Activities**: Individual .FIT files, Training Load (TSS equivalent), Distance, Watts.

## 🥗 SparkyFitness (Direct DB Access & Frontend)
*   **Purpose**: Source of truth for nutrition and body weight.
*   **Authentication**: Standard PostgreSQL connection via `SPARKY_HOST`, `SPARKY_USER`, etc.
*   **Frontend**: Served over **Tailscale HTTPS** on port 443 (proxied to internal port 3004).
*   **Security**: 
    *   Uses an `app.user_id` session variable to bypass Row Level Security (RLS) for the specific athlete.
    *   `BETTER_AUTH_ALLOWED_ORIGINS` is configured to match the Tailscale `.ts.net` domain for secure login.
*   **Data Points**:
    *   **Nutrition**: Total calories, Protein, Carbs, Fat, Fibre.
    *   **Granular Logs**: Specific food names and brands consumed.
    *   **Biometrics**: Daily morning weight measurements.

## 📊 Google Cloud Platform (Sheets & Drive)
*   **Service Account**: Authentication is handled via a `service_account.json` key file.
*   **Google Sheets API**: 
    *   Iterates through IDs in the `GOOGLE_SHEET_IDS` environment variable.
    *   Fetches "Active Energy" and "Body Fat %" that may be logged manually.
*   **Google Drive (via rclone)**:
    *   Synchronizes the `/opt/healthcoach/exports` folder to a remote Drive path (e.g., `Operation Outlive`).
    *   Manages the `daily_metrics_master.csv` file.

## 🤖 Telegram Bot API
*   **Library**: `python-telegram-bot`
*   **Authentication**: `TELEGRAM_BOT_TOKEN`.
*   **Roles**:
    *   **Bot**: Primary interaction.
    *   **Alerts**: Secondary token (`TELEGRAM_ALERTS_TOKEN`) used for system notifications via Watchtower or custom alerts.
