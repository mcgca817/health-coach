import os
import json
from datetime import date, timedelta
from app.db import get_cursor

def get_athlete_context():
    """
    Retrieves a verbose 7-day history of biometrics and nutrition, 
    excluding today and skipping days with no activity/nutrition logging.
    """
    # 1. Define the Date Range (Previous 7 full days)
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=6)
    
    with get_cursor() as cur:
        query = """
            SELECT 
                b.date, 
                b.weight_kg, 
                b.body_fat_pct, 
                b.hrv, 
                b.resting_hr, 
                b.sleep_hours,
                b.kcal_burned, 
                n.kcal_actual, 
                n.protein_actual_g,
                (COALESCE(b.kcal_burned, 0) - COALESCE(n.kcal_actual, 0)) as deficit
            FROM daily_biometrics b
            LEFT JOIN nutrition_actuals n ON b.date = n.date
            WHERE b.date BETWEEN %s AND %s
            ORDER BY b.date DESC;
        """
        cur.execute(query, (start_date, end_date))
        rows = cur.fetchall()

    if not rows:
        return "⚠️ No data found for the previous 7 days. Sync scripts may be offline."

    # 2. Filter logic: Skip days with 0 activity AND 0 nutrition (likely missing data)
    valid_rows = [r for r in rows if (r['kcal_burned'] or 0) > 0 or (r['protein_actual_g'] or 0) > 0]
    
    if not valid_rows:
        return "⚠️ No active or nutritional data found in the last 7 days."

    # 3. Calculate Accurate Averages (ignoring nulls/zeros)
    def get_avg(data_list):
        clean = [v for v in data_list if v and v > 0]
        return sum(clean) / len(clean) if clean else 0

    avg_weight = get_avg([r['weight_kg'] for r in valid_rows])
    avg_protein = get_avg([r['protein_actual_g'] for r in valid_rows])
    avg_hrv = get_avg([r['hrv'] for r in valid_rows])
    avg_deficit = sum(r['deficit'] or 0 for r in valid_rows) / len(valid_rows)

    # 4. Construct the Verbose Markdown Report
    report = [
        f"### ATHLETE STATUS REPORT (7-Day Performance Profile)",
        f"**Date Range:** {start_date} to {end_date}",
        "",
        f"**Performance Metrics (Averages):**",
        f"- **Weight:** {avg_weight:.2f} kg (Target: 75.0 kg)",
        f"- **Protein:** {avg_protein:.1f}g (Minimum Floor: 140g)",
        f"- **Net Deficit:** {avg_deficit:.0f} kcal/day",
        f"- **HRV Recovery:** {avg_hrv:.1f} ms",
        f"- **Protein Goal Status:** {'✅ MET' if avg_protein >= 140 else '❌ NOT MET'}",
        "",
        "**Detailed Historical Logs:**",
        "| Date | Weight | BF% | HRV | RHR | Sleep | Burn | Eat | Net | Prot |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for r in valid_rows:
        weight = f"{r['weight_kg']:.1f}" if r['weight_kg'] else "-- "
        bf = f"{r['body_fat_pct']:.1f}" if r['body_fat_pct'] else "-- "
        hrv = f"{r['hrv']}" if r['hrv'] else "-- "
        rhr = f"{r['resting_hr']}" if r['resting_hr'] else "-- "
        sleep = f"{r['sleep_hours']:.1f}" if r['sleep_hours'] else "-- "
        burn = r['kcal_burned'] or 0
        eat = r['kcal_actual'] or 0
        net = r['deficit'] or 0
        prot = f"{r['protein_actual_g']}g" if r['protein_actual_g'] else "0g"

        line = f"| {r['date']} | {weight}kg | {bf}% | {hrv}ms | {rhr}bpm | {sleep}h | {burn} | {eat} | {net} | {prot} |"
        report.append(line)

    report.append("\n*Note: Today's data is excluded to ensure report completeness.*")
    
    return "\n".join(report)

def generate_coaching_advice(user_query):
    """Entry point for the Telegram bot logic."""
    athlete_context = get_athlete_context()
    # In production, pass 'athlete_context' + 'user_query' to Claude API here
    return athlete_context
