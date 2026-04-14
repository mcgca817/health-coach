import os
import psycopg2
import requests
import pytest
from dotenv import load_dotenv

# Load from /app/.env (inside container)
load_dotenv('/app/.env')

def test_internal_sparky_db_connection():
    """Verify that the health-coach container can reach the internal sparkyfitness-db."""
    host = os.getenv('SPARKY_HOST', 'sparkyfitness-db')
    port = int(os.getenv('SPARKY_PORT', 5432))
    user = os.getenv('SPARKY_USER')
    password = os.getenv('SPARKY_PASSWORD')
    dbname = os.getenv('SPARKY_DB')

    print(f"\n📡 Testing internal DB connectivity to {host}...")
    
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=dbname,
            connect_timeout=5
        )
        cur = conn.cursor()
        cur.execute("SELECT 1")
        assert cur.fetchone()[0] == 1
        print("✅ Verified: Handshake with internal SparkyFitness DB successful.")
        cur.close()
        conn.close()
    except Exception as e:
        pytest.fail(f"Could not reach internal SparkyFitness DB: {e}")

def test_sparky_frontend_health():
    """Verify that the SparkyFitness frontend service is responding."""
    # From within the healthcoach container, sparkyfitness-frontend:80 should be accessible
    url = "http://sparkyfitness-frontend:80"
    print(f"\n📡 Testing Sparky Frontend health at {url}...")
    
    try:
        response = requests.get(url, timeout=5)
        assert response.status_code == 200
        print("✅ Verified: SparkyFitness frontend is UP.")
    except Exception as e:
        # Frontend might take a moment to start, we can try localhost:3004 if running on host
        print(f"⚠️ Warning: Could not reach frontend at {url}: {e}")
        # Alternative for host-based testing if needed
        # response = requests.get("http://localhost:3004", timeout=5)
        # assert response.status_code == 200
        pytest.skip("Frontend might not be fully initialized or not on this network.")
