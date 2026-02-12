"""
Interface with Anthropic Claude API.
"""
import os
import json
import anthropic
from dotenv import load_dotenv

# Force load the .env file to ensure keys are present
load_dotenv('/opt/healthcoach/.env')

CLIENT = anthropic.Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))

SYSTEM_PROMPT = """
You are an expert elite sports physiologist and nutritionist (PhD level).
Your client is a serious amateur athlete training for performance and longevity.

KEY METRICS DEFINITION:
- CTL (Chronic Training Load): "Fitness" - Long-term rolling average of training load (42 days).
- ATL (Acute Training Load): "Fatigue" - Short-term rolling average (7 days).
- TSB (Training Stress Balance): "Form" - (CTL - ATL). 
  - Positive (>0): Fresh / Tapered.
  - Negative (-10 to -30): Productive Training.
  - Very Negative (<-30): High Risk of Overtraining/Injury.
- HRV: Heart Rate Variability. Higher is generally better (recovery).
- Resting HR: Lower is generally better.

YOUR GOAL:
Optimize the daily plan for TOMORROW based on the client's current physiological state.
- If TSB is very low (<-30) or HRV is tanking -> Prescribe Recovery/Rest.
- If TSB is positive but Phase is "Building" -> Prescribe Hard Training.
- Adjust Calories based on the prescribed activity (Fuel the work).

OUTPUT FORMAT:
You must output ONLY valid JSON. No preamble, no markdown blocks.
"""

def generate_plan(context, constraints):
    """
    Send context to Claude and get a daily plan.
    """
    
    user_prompt = f"""
    CURRENT DATE: {context['date']}
    ACTIVE PHASE: {context['phase']['phase']} (Started: {context['phase'].get('start_date')})
    
    --- RECENT BIOMETRICS (Last 14 Days) ---
    (Includes Weight, HRV, Resting HR, and Training Load)
    {json.dumps(context['biometrics'], default=str, indent=2)}
    
    --- RECENT NUTRITION (Last 7 Days) ---
    {json.dumps(context['nutrition'], default=str, indent=2)}
    
    --- ACTIVE CONSTRAINTS (MUST OBEY) ---
    {constraints}
    
    --- TASK ---
    Generate a detailed plan for TOMORROW.
    1. Nutrition: Specific Macros.
    2. Training: Specific Workout.
    3. Reasoning: strictly based on the data (reference CTL/TSB/HRV trends).
    
    --- REQUIRED JSON OUTPUT ---
    {{
      "nutrition": {{ "kcal": 0, "protein": 0, "carbs": 0, "fat": 0, "refeed": false }},
      "training": {{ "workout_type": "string", "duration_minutes": 0, "intensity_zone": "string", "description": "string" }},
      "reasoning": "string"
    }}
    """
    
    try:
        message = CLIENT.messages.create(
            model="claude-3-5-sonnet-20240620", # Using Sonnet 3.5 for best reasoning
            max_tokens=1000,
            temperature=0.2, # Low temperature for consistent adherence to data
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        response_text = message.content[0].text
        return json.loads(response_text)
        
    except Exception as e:
        print(f"❌ LLM Error: {e}")
        return None
