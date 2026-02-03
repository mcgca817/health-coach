"""
Interface with Anthropic Claude API.
"""
import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv('/opt/healthcoach/.env')

CLIENT = anthropic.Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))

SYSTEM_PROMPT = """
You are an expert elite sports physiologist and nutritionist.
Your goal is to optimize the user's body composition and performance.
You must output ONLY valid JSON. No preamble.
"""

def generate_plan(context, constraints):
    """
    Send context to Claude and get a daily plan.
    """
    
    user_prompt = f"""
    Current Date: {context['date']}
    Phase: {context['phase']}
    
    Recent Biometrics:
    {json.dumps(context['biometrics'], default=str)}
    
    Training Load:
    {json.dumps(context['load'], default=str)}
    
    Active Constraints (MUST OBEY):
    {constraints}
    
    Task:
    Generate a plan for TOMORROW.
    1. Nutrition: Calories, Protein, Carbs, Fat.
    2. Training: Workout type, duration, intensity.
    3. Reasoning: Why this plan?
    
    Output Format (JSON):
    {{
      "nutrition": {{ "kcal": 2000, "protein": 180, "carbs": 200, "fat": 60, "refeed": false }},
      "training": {{ "workout_type": "cycling", "duration_minutes": 60, "intensity_zone": "Z2", "description": "Easy spin" }},
      "reasoning": "Data looks good, continue progression."
    }}
    """
    
    message = CLIENT.messages.create(
        model="claude-3-haiku-20240307", # Or claude-3-sonnet-20240229
        max_tokens=1000,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}]
    )
    
    response_text = message.content[0].text
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        print("Failed to decode JSON from Claude")
        return None
