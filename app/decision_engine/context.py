import os
from app.db import get_cursor
from datetime import datetime, timedelta

def get_athlete_context(days=7):
    """
    Fetches raw data from the local DB and formats it as a 
    structured summary for the LLM.
    """
    with get_cursor() as cur:
        # Fetch combined metrics for the requested window
        cur.execute("""
            SELECT 
                b.date, 
                b.weight_kg, 
                b.kcal_burned, 
                b.ctl, 
                b.tsb, 
                b.hrv,
                n.kcal_actual, 
                n.protein_actual_g
            FROM daily_biometrics b
            LEFT JOIN nutrition_actuals n ON b.date = n.date
            WHERE b.date >= CURRENT_DATE - %s * INTERVAL '1 day'
            ORDER BY b.date DESC
        """, (days,))
        
        rows = cur.fetchall()

    if not rows:
        return "No recent data found in the database."

    # Process metrics
    latest = rows[0]
    
    # Calculate averages for the window
    avg_protein = sum(r['protein_actual_g'] or 0 for r in rows) / days
    avg_deficit = sum((r['kcal_actual'] or 0) - (r['kcal_burned'] or 0) for r in rows if r['kcal_burned']) / days

    # Construct the context string
    context = [
        "### ATHLETE STATUS REPORT",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "**Current Biometrics (Latest):**",
        f"- Weight: {latest['weight_kg']} kg",
        f"- Fitness (CTL): {latest['ctl']}",
        f"- Form (TSB): {latest['tsb']} (Ready to train)" if latest['tsb'] > -10 else f"- Form (TSB): {latest['tsb']} (Recovery needed)",
        f"- HRV: {latest['hrv']} ms",
        "",
        "**Nutrition & Deficit (7-Day Averages):**",
        f"- Avg Protein: {avg_protein:.1f}g (Target: 140g)",
        f"- Avg Daily Deficit: {avg_deficit:.0f} kcal",
        f"- Protein Floor Met: {'✅' if avg_protein >= 140 else '❌'}",
        "",
        "**Recent Daily Log:**",
        "| Date | Burn (TDEE) | Intake | Net | Protein |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ]

    for r in rows[:5]: # Show last 5 days in a table
        burn = r['kcal_burned'] or 0
        intake = r['kcal_actual'] or 0
        net = intake - burn
        context.append(f"| {r['date']} | {burn} | {intake} | {net:+} | {r['protein_actual_g']}g |")

    return "\n".join(context)
