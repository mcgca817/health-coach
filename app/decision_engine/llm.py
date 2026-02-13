import os
import json
from datetime import date, timedelta
from app.db import get_cursor

def get_verbose_status():
    """
    Constructs a comprehensive performance report:
    1. 30-day biometric & nutrition table.
    2. 7-day granular food log.
    3. 7-day training summary.
    """
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago = today - timedelta(days=7)
    yesterday = today - timedelta(days=1)

    with get_cursor() as cur:
        # 1. 30-Day Biometrics
        cur.execute("""
            SELECT 
                b.date, b.weight_kg, b.body_fat_pct, b.hrv, b.resting_hr, b.sleep_hours,
                b.kcal_burned, n.kcal_actual, n.protein_actual_g,
                (COALESCE(b.kcal_burned, 0) - COALESCE(n.kcal_actual, 0)) as deficit
            FROM daily_biometrics b
            LEFT JOIN nutrition_actuals n ON b.date = n.date
            WHERE b.date >= %s AND b.date <= %s
            ORDER BY b.date DESC;
        """, (thirty_days_ago, yesterday))
        stats_rows = cur.fetchall()

        # 2. 7-Day Food Logs (Exact entries)
        cur.execute("""
            SELECT date, meal_name, entry_text, kcal_actual, protein_actual_g
            FROM nutrition_logs 
            WHERE date >= %s AND date <= %s
            ORDER BY date DESC, created_at ASC;
        """, (seven_days_ago, yesterday))
        food_logs = cur.fetchall()

        # 3. 7-Day Training Summary (Activities)
        cur.execute("""
            SELECT date, name, type, distance_km, moving_time_min, load, average_watts
            FROM activities
            WHERE date >= %s AND date <= %s
            ORDER BY date DESC;
        """, (seven_days_ago, yesterday))
        training_rows = cur.fetchall()

    return format_status_report(stats_rows, food_logs, training_rows)

def format_status_report(stats, food, training):
    if not stats:
        return "⚠️ No data found in the last 30 days."

    # Calculate Averages (30 days, skipping nulls)
    weights = [r['weight_kg'] for r in stats if r['weight_kg']]
    avg_weight = sum(weights) / len(weights) if weights else 0
    proteins = [r['protein_actual_g'] for r in stats if r['protein_actual_g']]
    avg_protein = sum(proteins) / len(proteins) if proteins else 0
    hrvs = [r['hrv'] for r in stats if r['hrv']]
    avg_hrv = sum(hrvs) / len(hrvs) if hrvs else 0
    avg_deficit = sum(r['deficit'] or 0 for r in stats) / len(stats)

    report = [
        "### ATHLETE STATUS REPORT (30-Day Profile)",
        f"**Weight:** {avg_weight:.2f}kg (Target: 75kg) | **HRV:** {avg_hrv:.1f}ms",
        f"**Avg Protein:** {avg_protein:.1f}g (Floor: 140g) | **Avg Deficit:** {avg_deficit:.0f}kcal",
        f"**Protein Goal Status:** {'✅ MET' if avg_protein >= 140 else '❌ NOT MET'}",
        "",
        "**30-Day Historical Logs:**",
        "| Date | Weight | HRV | Burn | Eat | Net | Prot |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for r in stats:
        weight = f"{r['weight_kg']:.1f}" if r['weight_kg'] else "-- "
        hrv = f"{r['hrv']}" if r['hrv'] else "-- "
        burn = r['kcal_burned'] or 0
        eat = r['kcal_actual'] or 0
        net = r['deficit'] or 0
        prot = f"{r['protein_actual_g']}g" if r['protein_actual_g'] else "0g"
        report.append(f"| {r['date']} | {weight} | {hrv} | {burn} | {eat} | {net} | {prot} |")

    report.append("\n**--- 7-DAY FOOD LOG ---**")
    current_date = None
    if not food:
        report.append("_No food logs found for this period._")
    for f in food:
        if f['date'] != current_date:
            current_date = f['date']
            report.append(f"\n**{current_date}**")
        report.append(f"- {f['meal_name']}: {f['entry_text']} ({f['kcal_actual']} kcal, {f['protein_actual_g']}g P)")

    report.append("\n**--- 7-DAY TRAINING SUMMARY ---**")
    if not training:
        report.append("_No activity logs found for this period._")
    for t in training:
        watts = f"{t['average_watts']}W" if t['average_watts'] else "N/A"
        report.append(f"- {t['date']}: {t['name']} ({t['type']}) - {t['distance_km']}km, {t['moving_time_min']}m, {t['load']} Load, {watts}")

    return "\n".join(report)

def generate_coaching_advice(user_query):
    # This remains for the AI chat interaction
    athlete_context = get_verbose_status()
    return athlete_context
