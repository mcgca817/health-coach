# ETL (data ingestion)

Purpose: ingest and normalize data from fitness services into the central database.

Locations
- `app/etl/` — ETL helpers used by the app runtime (e.g. `sparkyfitness.py`, `intervals_icu.py`).
- `etl/` — repository-level ETL scripts (may contain standalone jobs or historical scripts).

Typical flow
1. Fetch raw data from provider APIs (Intervals.icu, SparkyFitness).
2. Normalize timestamps, activity metrics, and nutrition entries.
3. Upsert into the central Postgres schema used by `app/db.py`.

Running ETL
- ETL scripts expect database credentials via the same `/opt/healthcoach/.env` used by the app.
- For ad-hoc runs, call the script directly, e.g.: `python -m app.etl.sparkyfitness` (adapt to module path as needed).
