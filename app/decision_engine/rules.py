"""
Hard rules and circuit breakers.
Ensures safety checks are run against validated numeric data.
"""

def safe_float(value, default=None):
    """Safely convert database values to float, handling None and strings."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def check_circuit_breakers(context):
    """
    Analyze context and return a list of triggered constraints.
    Returns: (triggered_rules_list, reasoning_string)
    """
    triggers = []
    reasoning = []
    
    biometrics = context.get('biometrics', [])
    rules = context.get('rules', {})
    
    # Defaults if no data
    if not biometrics:
        return ["no_data"], "No biometric data available to assess readiness."

    today = biometrics[0] # Most recent entry
    
    # --- 1. Check HRV (Circuit Breaker) ---
    # Threshold: If HRV is critically low (< 30ms), we force a rest day.
    hrv = safe_float(today.get('hrv'))
    
    if hrv is not None and hrv < 30:
        triggers.append("low_hrv")
        reasoning.append(f"HRV is critically low ({int(hrv)}ms). Force Rest/Recovery.")

    # --- 2. Check Sleep Debt ---
    # Threshold: If avg sleep over last 3 days < 5.5 hours, cap intensity.
    recent_sleep_values = []
    for day_data in biometrics[:3]:
        val = safe_float(day_data.get('sleep_hours'))
        if val is not None:
            recent_sleep_values.append(val)
            
    if recent_sleep_values:
        avg_sleep = sum(recent_sleep_values) / len(recent_sleep_values)
        if avg_sleep < 5.5:
            triggers.append("high_sleep_debt")
            reasoning.append(f"Sleep debt high (Avg {avg_sleep:.1f}h). Intensity capped.")

    # --- 3. Check Training Stress Balance (TSB) ---
    # If TSB is very negative (<-30), risk of injury is high.
    load = context.get('load', {})
    tsb = safe_float(load.get('tsb'))
    
    if tsb is not None and tsb < -30:
        triggers.append("high_fatigue")
        reasoning.append(f"Training Stress Balance is very low ({int(tsb)}). Risk of overtraining.")

    return triggers, "; ".join(reasoning)
