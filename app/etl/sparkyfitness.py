"""ETL for SparkyFitness nutrition data."""
import os
import sys
import psycopg2
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_cursor, log_job_start, log_job_success, log_job_failure
from dotenv import load_dotenv

load_dotenv('/opt/healthcoach/.env')

def get_sparky_connection():
    """Connect to SparkyFitness database."""
    return psycopg2.connect(
        host=os.getenv('SPARKY_HOST'),
        port=int(os.getenv('SPARKY_PORT', 5432)),
        user=os.getenv('SPARKY_USER'),
        password=os.getenv('SPARKY_PASSWORD'),
        database=os.getenv('SPARKY_DB')
    )

def fetch_nutrition_data(days_back=7):
    """
    Fetch nutrition data from SparkyFitness.
    Note: You MUST update the query below to match your actual schema.
    """
    conn = get_sparky_connection()
    cur = conn.cursor()
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back)

    # TODO: Update this query based on your actual SparkyFitness schema
    query = """
        SELECT
            entry_date::date as date,
            SUM(calories) as kcal,
            SUM(protein) as protein_g,
            SUM(carbs) as carbs_g,
            SUM(fat) as fat_g,
            SUM(alcohol) as alcohol_g,
            COUNT(DISTINCT meal_id) as meals_count
        FROM food_diary
        WHERE entry_date >= %s AND entry_date <= %s
        GROUP BY entry_date::date
        ORDER BY entry_date::date
    """

    try:
        cur.execute(query, (start_date, end_date))
        results = cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return results

def import_nutrition():
    """Import nutrition data into our database."""
    data = fetch_nutrition_data(days_back=30)
    records = 0
    with get_cursor(dict_cursor=False) as cur:
        for row in data:
            # Unpack based on the query columns
            date, kcal, protein, carbs, fat, alcohol, meals = row
            
            cur.execute("""
                INSERT INTO nutrition_actuals (
                    date, kcal_actual, protein_actual_g, carbs_actual_g,
                    fat_actual_g, alcohol_g, meals_count
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (date) DO UPDATE SET
                    kcal_actual = EXCLUDED.kcal_actual,
                    protein_actual_g = EXCLUDED.protein_actual_g,
                    carbs_actual_g = EXCLUDED.carbs_actual_g,
                    fat_actual_g = EXCLUDED.fat_actual_g,
                    alcohol_g = EXCLUDED.alcohol_g,
                    meals_count = EXCLUDED.meals_count,
                    updated_at = CURRENT_TIMESTAMP
            """, (date, kcal, protein, carbs, fat, alcohol, meals))
            records += 1
    return records

def main():
    """Main ETL process."""
    job_name = 'etl_sparky_daily'
    run_id = log_job_start(job_name)
    try:
        print(f"Starting SparkyFitness ETL...")
        records = import_nutrition()
        print(f"Imported {records} nutrition records")
        log_job_success(run_id, records)
        print(f"ETL completed successfully")
    except Exception as e:
        error_msg = str(e)
        log_job_failure(run_id, error_msg)
        print(f"ETL failed: {error_msg}")
        print("\nIMPORTANT: You need to update the SQL query in this file")
        print("based on your actual SparkyFitness database schema.")
        sys.exit(1)

if __name__ == '__main__':
    main()
