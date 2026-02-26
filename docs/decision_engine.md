# `decision_engine` package

Purpose: constructs athlete-focused performance reports and planning. The package contains logic for multi-day reports, LLM integration helpers, and rule-based reasoning.

Key files
- `app/decision_engine/llm.py` — report composition helpers used by the bot. Exposes `get_verbose_status()` and `get_today_status()` functions returning markdown-friendly strings.
- `app/decision_engine/main.py` — entry point. Currently acts as a maintenance-mode bypass so systemd/cron jobs exit cleanly while logic is being refactored.
- `app/decision_engine/rules.py` — domain rules (guardrails, thresholds) used by the engine.
- `app/decision_engine/context.py` — structures to pass contextual inputs into the LLM/rules.

Notes
- `llm.py` reads from the database (via `app/db.py`) to build the 30-day metrics and training summaries.
- When re-enabling production decision logic, ensure proper error handling and rate limits are in place for any LLM calls.
