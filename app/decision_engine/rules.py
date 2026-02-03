"""
Hard rules and circuit breakers.
"""

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
        return [], "No biometric data available."

    today = biometrics[0] # Most recent
    
    # 1. Check HRV (Circuit Breaker)
    # If HRV < (baseline - 1.5 * sigma), force rest
    # Note: For simplicity, we assume 'hrv' in DB is raw ms.
    # In a real system, you'd calculate rolling baseline.
    # Here we simulate a simple check: is HRV < 30ms (panic threshold)?
    if today.get('hrv') and today['hrv'] < 30:
        triggers.append("low_hrv")
        reasoning.append(f"HRV ({today['hrv']}) is critically low. Force Rest.")

    # 2. Check Sleep Debt
    # If avg sleep last 3 days < 5 hours
    recent_sleep = [b['sleep_hours'] for b in biometrics[:3] if b.get('sleep_hours')]
    if recent_sleep and (sum(recent_sleep) / len(recent_sleep)) < 5.0:
        triggers.append("high_sleep_debt")
        reasoning.append("Average sleep < 5h. Intensity cap applied.")

    # 3. Protein Compliance
    # This isn't a hard stop, but a flag for the LLM
    protein_floor = rules.get('protein_floor_g_per_kg', 1.6)
    # logic to check protein would go here...

    return triggers, "; ".join(reasoning)
