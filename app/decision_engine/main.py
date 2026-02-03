"""
Main entry point for the Decision Engine.
"""
import sys
import os
import json

# Add parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_cursor, log_job_start, log_job_success, log_job_failure
from decision_engine.context import build_context
from decision_engine.rules import check_circuit_breakers
from decision_engine.llm import generate_plan

def save_plan(plan_json, context, constraints):
    """Save the generated plan to the database."""
    date = context['date'] # This is today, usually we plan for tomorrow. 
    # For simplicity in this guide, we log it as today's decision for tomorrow.
    
    with get_cursor() as cur:
        # 1. Save to plans_daily
        cur.execute("""
            INSERT INTO plans_daily 
            (date, phase, plan_json, llm_reasoning, hard_constraints_triggered)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (date) DO UPDATE SET
            plan_json = EXCLUDED.plan_json,
            llm_reasoning = EXCLUDED.llm_reasoning,
            updated_at = CURRENT_TIMESTAMP
        """, (
            date, 
            context['phase']['phase'], 
            json.dumps(plan_json), 
            plan_json.get('reasoning', ''),
            constraints[0] # The list of triggers
        ))
        
        # 2. Save Nutrition Targets
        nut = plan_json['nutrition']
        cur.execute("""
            INSERT INTO nutrition_targets
            (date, kcal_target, protein_target_g, carbs_target_g, fat_target_g, refeed)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (date) DO UPDATE SET
            kcal_target = EXCLUDED.kcal_target,
            protein_target_g = EXCLUDED.protein_target_g
        """, (
            date, nut['kcal'], nut['protein'], nut['carbs'], nut['fat'], nut['refeed']
        ))

def main():
    job_name = 'decision_engine_daily'
    run_id = log_job_start(job_name)
    
    try:
        print("1. Building Context...")
        context = build_context()
        
        print("2. Checking Rules...")
        triggers, reasoning = check_circuit_breakers(context)
        if triggers:
            print(f"   triggers active: {triggers}")
        
        print("3. Generating Plan with Claude...")
        plan = generate_plan(context, f"Triggers: {triggers}. Reasoning: {reasoning}")
        
        if plan:
            print("4. Saving Plan...")
            save_plan(plan, context, (triggers, reasoning))
            log_job_success(run_id, 1)
            print("Success! Plan Generated.")
            print(json.dumps(plan, indent=2))
        else:
            raise Exception("LLM returned empty plan")
            
    except Exception as e:
        log_job_failure(run_id, str(e))
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
