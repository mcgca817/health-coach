import os
from datetime import datetime, date, timedelta # <--- Added datetime
from app.db import get_cursor

def get_verbose_status():
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago = today - timedelta(days=7)
    yesterday = today - timedelta(days=1)
    
    # Capture exact time of report generation
    now_str = datetime.now().strftime("%H:%M:%S")

    with get_cursor() as cur:
        # 1. Fetch 30-Day Table & Load Metrics
        cur.execute("""
            SELECT b.date, b.weight_kg, b.hrv, b.ctl, b.atl, b.tsb,
                   b.kcal_burned, n.kcal_actual, n.protein_actual_g,
                   (COALESCE(b.kcal_burned, 0) - COALESCE(n.kcal_actual, 0)) as deficit
            FROM daily_biometrics b
            LEFT JOIN nutrition_actuals n ON b.date = n.date
            WHERE b.date >= %s AND b.date <= %s
            ORDER BY b.date DESC;
        """, (thirty_days_ago, yesterday))
        stats = cur.fetchall()

        # 2. Fetch 7-Day GRANULAR Food Logs
        cur.execute("""
            SELECT date, entry_text, kcal_actual, protein_actual_g, carbs_actual_g, fat_actual_g
            FROM nutrition_logs
            WHERE date >= %s AND date <= %s
            ORDER BY date DESC, kcal_actual DESC;
        """, (seven_days_ago, yesterday))
        food_logs = cur.fetchall()

        # 3. Fetch 7-Day Training Activities
        cur.execute("""
            SELECT date, name, type, distance_km, moving_time_min, load, average_watts
            FROM activities
            WHERE date >= %s AND date <= %s
            ORDER BY date DESC;
        """, (seven_days_ago, yesterday))
        training = cur.fetchall()

    return format_report(stats, food_logs, training, now_str)

def format_report(stats, food, training, now_str):
    if not stats: return "No data found."
    
    # Filter out 0-protein days for the average
    valid_protein_days = [r['protein_actual_g'] for r in stats if (r['protein_actual_g'] or 0) > 0]
    avg_protein = sum(valid_protein_days) / len(valid_protein_days) if valid_protein_days else 0.0

    curr = stats[0]
    report = [
        f"### 🛡️ MCPATTY PERFORMANCE STATUS (Updated: {now_str})", # <--- Timestamp Added
        f"**Fitness (CTL):** {curr['ctl'] or 0} | **Fatigue (ATL):** {curr['atl'] or 0}",
        f"**Form (TSB):** {curr['tsb'] or 0}",
        f"**Avg Protein (Active Days):** {avg_protein:.1f}g",
        "",
        "**📊 30-DAY BIOMETRICS**",
        "| Date | Weight | HRV | Burn | Eat | Net | Prot |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for r in stats:
        w = f"{r['weight_kg']:.1f}" if r['weight_kg'] else "--"
        report.append(f"| {r['date']} | {w} | {r['hrv'] or '--'} | {r['kcal_burned'] or 0} | {r['kcal_actual'] or 0} | {r['deficit'] or 0} | {r['protein_actual_g'] or 0}g |")

    report.append("\n**🥩 7-DAY FOOD DETAIL**")
    if not food:
        report.append("_No detailed food logs available._")
    
    current_date = None
    for f in food:
        if f['date'] != current_date:
            report.append(f"\n**{f['date']}**")
            current_date = f['date']
        
        p = float(f['protein_actual_g'] or 0)
        c = float(f['carbs_actual_g'] or 0)
        ft = float(f['fat_actual_g'] or 0)
        
        report.append(f"- {f['entry_text']}: {f['kcal_actual']}kcal (P:{p:.0f} C:{c:.0f} F:{ft:.0f})")

    report.append("\n**🚵 7-DAY TRAINING SUMMARY**")
    if not training:
        report.append("_No activity logs available._")
    for t in training:
        pwr = f"{t['average_watts']}W" if t.get('average_watts') else "N/A"
        report.append(f"- {t['date']}: {t['name']} | {t['distance_km']}km | {t['load']} Load | {pwr}")

    return "\n".join(report)
