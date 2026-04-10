"""
Database Utility Layer.
Provides centralized connection management, cursor handling, and job logging.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv

# Load server-side environment variables
load_dotenv('/opt/healthcoach/.env')

def get_db_connection():
    """
    Creates and returns a new connection to the local PostgreSQL database.
    Defaults to 'healthcoach' user/db if environment variables are missing.
    """
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        user=os.getenv('POSTGRES_USER', 'healthcoach'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('POSTGRES_DB', 'healthcoach')
    )

@contextmanager
def get_cursor(dict_cursor=True):
    """
    Context manager for database cursors.
    - Handles automatic commit on success and rollback on error.
    - Supports both RealDictCursor (for name-based access) and standard cursors.
    
    Usage:
        with get_cursor() as cur:
            cur.execute("SELECT...")
    """
    conn = get_db_connection()
    cursor_factory = RealDictCursor if dict_cursor else None
    cursor = conn.cursor(cursor_factory=cursor_factory)
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def log_job_start(job_name):
    """
    Initializes a record in run_history to track background job performance.
    Returns the unique run_id.
    """
    with get_cursor(dict_cursor=False) as cur:
        cur.execute("""
            INSERT INTO run_history (job_name, started_at, status)
            VALUES (%s, CURRENT_TIMESTAMP, 'running')
            RETURNING id
        """, (job_name,))
        return cur.fetchone()[0]

def log_job_success(run_id, records_processed=None):
    """Marks a specific job run as successful and logs the volume of data handled."""
    with get_cursor(dict_cursor=False) as cur:
        cur.execute("""
            UPDATE run_history
            SET finished_at = CURRENT_TIMESTAMP,
                status = 'success',
                records_processed = %s
            WHERE id = %s
        """, (records_processed, run_id))

def log_job_failure(run_id, error_message):
    """Logs the crash details of a failed job run for troubleshooting."""
    with get_cursor(dict_cursor=False) as cur:
        cur.execute("""
            UPDATE run_history
            SET finished_at = CURRENT_TIMESTAMP,
                status = 'failure',
                error_message = %s
            WHERE id = %s
        """, (error_message, run_id))
