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
    print(f"\n📡 Testing: Database connectivity to {os.getenv('POSTGRES_DB')}...")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        assert cur.fetchone()[0] == 1
        print("✅ Verified: Postgres container is accepting connections.")
        
        cur.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';")
        tables = [row[0] for row in cur.fetchall()]
        
        print(f"📊 Found {len(tables)} tables in schema.")
        
        required_tables = ['daily_biometrics', 'training_load', 'activities', 'nutrition_actuals', 'journal_entries']
        for table in required_tables:
            assert table in tables, f"CRITICAL: Required table '{table}' is missing!"
            print(f"   -> Table '{table}': OK")
        
        # Check row counts for a sanity check
        cur.execute("SELECT COUNT(*) FROM daily_biometrics")
        count = cur.fetchone()[0]
        print(f"📈 Total Biometric records: {count}")
        
        cur.close()
        conn.close()
    except psycopg2.OperationalError as e:
        print(f"⚠️ Warning: Postgres connection failed: {e}")
        pytest.skip("Local postgres not accessible.")

def test_sparky_connection():
    """Verify connection to SparkyFitness (if configured in environment)."""
    host = os.getenv('SPARKY_HOST')
    print(f"\n📡 Testing: External connectivity to SparkyFitness ({host})...")
    
    if not host:
        print("⏭️ Skipped: SPARKY_HOST not set in environment.")
        pytest.skip("SPARKY_HOST not set")
    
    try:
        conn = psycopg2.connect(
            host=host,
            port=int(os.getenv('SPARKY_PORT', 5432)),
            user=os.getenv('SPARKY_USER'),
            password=os.getenv('SPARKY_PASSWORD'),
            database=os.getenv('SPARKY_DB'),
            connect_timeout=5
        )
        cur = conn.cursor()
        cur.execute("SELECT 1")
        assert cur.fetchone()[0] == 1
        print("✅ Verified: Handshake with SparkyFitness DB successful.")
        cur.close()
        conn.close()
    except psycopg2.OperationalError as e:
        print(f"❌ Failed: Could not reach SparkyFitness database: {e}")
        pytest.fail(f"SparkyFitness Connection Error: {e}")
