# 🧪 Testing Suite

Verification is performed using **Pytest** and is divided into Unit and Integration tests.

## 🧱 Unit Tests (`tests/unit/`)
These tests verify individual logic components without requiring an external database or network connection.

*   **`test_llm.py`**:
    *   Verifies the `format_report` function.
    *   Ensures Markdown tables are generated correctly.
    *   Checks that EMA (Exponential Moving Average) calculations for body weight are accurate.
    *   Handles edge cases (e.g., zero data rows).

## 🔗 Integration Tests (`tests/integration/`)
These tests run on the target server and verify that the application can interact with its environment.

*   **`test_db_sync.py`**:
    *   **Postgres**: Checks that the local Docker container is up and responding. Verifies all required tables (`activities`, `training_load`, etc.) are present in the `public` schema.
    *   **SparkyFitness**: Performs a real-world handshake with the external SparkyFitness database using the credentials in `.env`.

## 📈 Running Tests Manually

**On your Mac (Unit Tests only):**
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/app
pytest tests/unit/
```

**On the Server (Full Suite):**
```bash
cd /opt/healthcoach
venv/bin/python3 -m pytest tests/ -v -s
```
The `-s` flag is recommended to see detailed internal logging about database row counts and connection status.
