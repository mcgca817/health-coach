import os
from datetime import datetime, date, timedelta
from app.db import get_cursor


# In app/decision_engine/llm.py

def get_verbose_status():
    """
    Constructs the McPatty Performance Dashboard (30-Day History).
    """
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago = today - timedelta(days=7)
    
    # Capture exact time of report generation
    now_str = datetime.now().strftime("%H:%M:%S")

    with get_cursor() as cur:
        # 1. Fetch 30-Day Table
        cur.execute("""
            SELECT 
                b.date, b.weight_kg, b.body_fat_pct, b.sleep_hours, b.hrv, b.kcal_burned,
                t.ctl, t.atl, t.tsb,
                n.kcal_actual, n.protein_actual_g, n.carbs_actual_g, n.fat_actual_g, n.fibre_actual_g
            FROM daily_biometrics b
            LEFT JOIN nutrition_actuals n ON b.date = n.date
            LEFT JOIN training_load t ON b.date = t.date
            WHERE b.date >= %s AND b.date <= %s
            ORDER BY b.date ASC;
        """, (thirty_days_ago, today))
        stats = cur.fetchall()

        # 2. Fetch 7-Day Training Activities
        cur.execute("""
            SELECT date, name, type, distance_km, moving_time_min, load, average_watts
            FROM activities
            WHERE date >= %s AND date <= %s
            ORDER BY date DESC;
        """, (seven_days_ago, today))
        training = cur.fetchall()

        # 3. Fetch 7-Day Journal Entries
        cur.execute("""
            SELECT date, entry_text, mood
            FROM journal_entries
            WHERE date >= %s AND date <= %s
            ORDER BY date DESC;
        """, (seven_days_ago, today))
        journals = cur.fetchall()

    # Calculate 7-Day Weighted Average (Exponential Moving Average) for Weight
    ema = None
    for r in stats:
        w = r['weight_kg']
        if w is not None:
            w = float(w)
            if ema is None:
                ema = w
            else:
                ema = (w * 0.25) + (ema * 0.75)
        r['weight_ema'] = ema

    # Reverse stats so the most recent day is at the top of the table
    stats.reverse()

    # PASSING 4 ARGUMENTS HERE
    return format_report(stats, training, journals, now_str)

# ACCEPTING 4 ARGUMENTS HERE
def format_report(stats, training, journals, now_str):
    if not stats: return "No data found."
    
    valid_protein_days = [r['protein_actual_g'] for r in stats if (r['protein_actual_g'] or 0) > 0]
    avg_protein = sum(valid_protein_days) / len(valid_protein_days) if valid_protein_days else 0.0

    curr = stats[0]
    report = [
        f"### 🛡️ MCPATTY PERFORMANCE STATUS (Updated: {now_str})",
        f"**Fitness (CTL):** {curr['ctl'] or 0} | **Fatigue (ATL):** {curr['atl'] or 0}",
        f"**Form (TSB):** {curr['tsb'] or 0}",
        f"**Avg Protein (Active Days):** {avg_protein:.1f}g",
        "",
        "**📊 30-DAY METRICS**",
        "| Date | Wt | 7dAvg | BF% | Slp | HRV | Eat | Burn | P | C | F | Fib |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for r in stats:
        dt_str = r['date'].strftime('%m-%d') if hasattr(r['date'], 'strftime') else str(r['date'])[-5:]
        
        w = f"{r['weight_kg']:.1f}" if r['weight_kg'] else "--"
        w_avg = f"{r['weight_ema']:.1f}" if r.get('weight_ema') else "--"
        bf = f"{r['body_fat_pct']:.1f}" if r.get('body_fat_pct') is not None else "--"
        slp = f"{r['sleep_hours']:.1f}" if r.get('sleep_hours') else "--"
        hrv = r['hrv'] or "--"
        
        eat = r['kcal_actual'] or 0
        burn = r.get('kcal_burned') or 0
        p = f"{float(r['protein_actual_g'] or 0):.0f}"
        c = f"{float(r['carbs_actual_g'] or 0):.0f}"
        f_macro = f"{float(r['fat_actual_g'] or 0):.0f}"
        fib = f"{float(r['fibre_actual_g'] or 0):.0f}"
        
        report.append(f"| {dt_str} | {w} | {w_avg} | {bf} | {slp} | {hrv} | {eat} | {burn} | {p} | {c} | {f_macro} | {fib} |")

    # ADDING THE JOURNAL OUTPUT HERE
    report.append("\n**📓 7-DAY JOURNAL**")
    if not journals:
        report.append("_No recent journal entries._")
    else:
        for j in journals:
            mood_str = f" [{j['mood']}]" if j.get('mood') else ""
            report.append(f"- {j['date']}{mood_str}: {j['entry_text']}")

    report.append("\n**🚵 7-DAY TRAINING SUMMARY**")
    if not training:
        report.append("_No activity logs available._")
    for t in training:
        pwr = f"{t['average_watts']}W" if t.get('average_watts') else "N/A"
        report.append(f"- {t['date']}: {t['name']} | {t['distance_km']}km | {t['load']} Load | {pwr}")

    return "\n".join(report)


def get_today_status():
    """
    Returns a snapshot for TODAY only.
    Uses DISTINCT to remove duplicate workouts from multiple sources.
    """
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)
    now_str = datetime.now().strftime("%H:%M:%S")

    with get_cursor() as cur:
        # 1. Fetch 30-Day Stats (Needed ONLY for the Header averages/metrics)
        cur.execute("""
            SELECT b.date, t.ctl, t.atl, t.tsb, n.protein_actual_g
            FROM daily_biometrics b
            LEFT JOIN nutrition_actuals n ON b.date = n.date
            LEFT JOIN training_load t ON b.date = t.date
            WHERE b.date >= %s AND b.date <= %s
            ORDER BY b.date DESC;
        """, (thirty_days_ago, today))
        stats = cur.fetchall()

        # 2. Fetch TODAY'S Food
        cur.execute("""
            SELECT entry_text, kcal_actual, protein_actual_g, carbs_actual_g, fat_actual_g, fibre_actual_g
            FROM nutrition_logs
            WHERE date = %s
            ORDER BY kcal_actual DESC;
        """, (today,))
        todays_food = cur.fetchall()

        # 3. Fetch TODAY'S Training
        cur.execute("""
            SELECT DISTINCT name, distance_km, load, average_watts
            FROM activities
            WHERE date = %s
            ORDER BY load DESC;
        """, (today,))
        todays_training = cur.fetchall()

    if not stats: return "No data available."

    # --- Header Math ---
    curr = stats[0]
    valid_protein_days = [r['protein_actual_g'] for r in stats if (r['protein_actual_g'] or 0) > 0]
    avg_protein = sum(valid_protein_days) / len(valid_protein_days) if valid_protein_days else 0.0
    
    # --- Build Report ---
    report = [
        f"### 🛡️ MCPATTY TODAY ({now_str})",
        f"**Fitness (CTL):** {curr['ctl'] or 0} | **Fatigue (ATL):** {curr['atl'] or 0}",
        f"**Form (TSB):** {curr['tsb'] or 0}",
        f"**Avg Protein (30d):** {avg_protein:.1f}g",
        "",
        "**🥩 TODAY'S NUTRITION**"
    ]

    total_kcal = 0
    total_prot = 0

    if not todays_food:
        report.append("_Nothing logged yet._")
    else:
        for f in todays_food:
            p = float(f['protein_actual_g'] or 0)
            c = float(f['carbs_actual_g'] or 0)
            ft = float(f['fat_actual_g'] or 0)
            fib = float(f['fibre_actual_g'] or 0)
            kcal = f['kcal_actual'] or 0
            
            total_kcal += kcal
            total_prot += p
            
            report.append(f"- {f['entry_text']}: {kcal}kcal (P:{p:.0f} C:{c:.0f} F:{ft:.0f} Fib:{fib:.0f})")
        
        # Daily Totals Footer
        report.append(f"\n**TOTAL:** {total_kcal} kcal | **{total_prot:.0f}g Protein**")

    report.append("\n**🚵 TODAY'S TRAINING**")
    if not todays_training:
        report.append("_No training recorded today._")
    else:
        for t in todays_training:
            pwr = f"{t['average_watts']}W" if t.get('average_watts') else "N/A"
            report.append(f"- {t['name']} | {t['distance_km']}km | {t['load']} Load | {pwr}")

    return "\n".join(report)
