# 🏗️ Core Architecture

The McPatty Performance Coach is designed as a modular suite of services that communicate via a shared PostgreSQL database.

## 🔄 Data Flow

1.  **Ingestion Layer (`app/sync/`)**:
    *   `main.py` acts as the orchestrator.
    *   API clients (`intervals.py`, `sparky.py`, `sync_sheets.py`) fetch data from external providers.
    *   Data is "Upserted" (Inserted or Updated on Conflict) into Postgres to maintain a consistent state.

2.  **Storage Layer (PostgreSQL)**:
    *   `daily_biometrics`: Core health markers (HRV, Sleep, Weight).
    *   `training_load`: Fitness trends (CTL, ATL, TSB).
    *   `activities`: Detailed workout metadata.
    *   `nutrition_actuals`: Aggregated daily calorie and macro totals.
    *   `nutrition_logs`: Granular line-item food entries.

3.  **Visualization Layer (`app/bot/` & `app/decision_engine/`)**:
    *   `bot/main.py` handles the Telegram API and user commands.
    *   `decision_engine/llm.py` performs complex SQL joins and EMA (Exponential Moving Average) calculations to generate readable reports.

4.  **Export Layer (`app/sync/daily_export.py`)**:
    *   Flattens the relational database into a `daily_metrics_master.csv`.
    *   Uses **rclone** to synchronize these files to Google Drive for permanent storage and external analysis.

## 🛠️ Key Technologies

*   **Python 3.13+**: Core application logic.
*   **PostgreSQL 16**: Primary relational data store.
*   **Docker & Docker Compose**: Containerization of the database.
*   **Ansible**: Infrastructure as Code (IaC) for automated deployment.
*   **Systemd**: Manages background timers and long-running bot services.
*   **rclone**: Cloud storage synchronization.
