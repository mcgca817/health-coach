import os
import sys
import psycopg2
import pytest
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from app.db import get_db_connection

# Fallback for local testing vs server testing
if os.path.exists('/opt/healthcoach/.env'):
    load_dotenv('/opt/healthcoach/.env')
else:
    load_dotenv()

def test_local_postgres_connection():
    """Verify the main application database is accessible and has tables."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        assert cur.fetchone()[0] == 1
        
        cur.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';")
        tables = [row[0] for row in cur.fetchall()]
        
        assert 'daily_biometrics' in tables
        assert 'training_load' in tables
        assert 'activities' in tables
        
        cur.close()
        conn.close()
    except psycopg2.OperationalError:
        pytest.skip("Local postgres not accessible - likely running outside of server environment.")

def test_sparky_connection():
    """Verify connection to SparkyFitness (if configured in environment)."""
    if not os.getenv('SPARKY_HOST'):
        pytest.skip("SPARKY_HOST not set")
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('SPARKY_HOST'),
            port=int(os.getenv('SPARKY_PORT', 5432)),
            user=os.getenv('SPARKY_USER'),
            password=os.getenv('SPARKY_PASSWORD'),
            database=os.getenv('SPARKY_DB'),
            connect_timeout=3
        )
        cur = conn.cursor()
        cur.execute("SELECT 1")
        assert cur.fetchone()[0] == 1
        cur.close()
        conn.close()
    except psycopg2.OperationalError as e:
        pytest.fail(f"Could not connect to SparkyFitness database: {e}")
