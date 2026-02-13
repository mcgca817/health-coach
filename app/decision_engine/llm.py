import os
import sys
from anthropic import Anthropic
from dotenv import load_dotenv

# Ensure the app root is in the path for internal imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.decision_engine.context import get_athlete_context

# Load environment variables - prioritizing the standard production path
load_dotenv('/opt/healthcoach/.env')

def get_coaching_advice():
    """
    Retrieves current athlete context and passes it to Claude-3.5-Sonnet
    to generate tactical coaching advice.
    """
    # Check for both possible names in the .env
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
    
    if not api_key:
        return "❌ ERROR: No API Key found. Check .env for CLAUDE_API_KEY or ANTHROPIC_API_KEY."

    client = Anthropic(api_key=api_key)
    
    # 1. Fetch the data report generated from your local Postgres DB
    report = get_athlete_context(days=7)
    
    # 2. Define the Coaching Persona and Cameron's specific constraints
    system_prompt = """
    You are 'McPatty Coach', an elite, data-driven performance coach. 
    You are coaching Cameron, a CISO training for the Whaka 50 MTB race.
    
    CAMERON'S CORE GOALS:
    - Reach 75kg by May 2026 (40th Birthday).
    - Achieve a 250W FTP for the Whaka 50.
    - Strict 140g daily protein floor to maintain structural integrity.
    
    DIETARY CONSTRAINTS:
    - NO almonds, chickpeas, or apricots (allergies/aversions).
    - Diet style: High protein, controlled caloric deficit.
    
    YOUR COACHING STYLE:
    - Tactical and brief (He is a busy CISO).
    - Slightly witty/dry.
    - Never generic. If he's missing his protein floor, call it out. 
    - If his TSB (Form) is negative, suggest recovery. 
    - If he has a surplus without a big training load, warn him about the 75kg goal.
    """

    user_prompt = f"""
    Cameron's Weekly Status Report:
    
    {report}
    
    Based on this specific data, give me a tactical priority for today and a 
    suggestion for the next meal.
    """

    try:
        # 3. Call Claude 3.5 Sonnet
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=600,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return response.content[0].text

    except Exception as e:
        return f"❌ Coaching Engine Error: {str(e)}"

if __name__ == "__main__":
    # Standard test execution
    print("\n--- MCPATTY COACH IS ANALYZING ---")
    print(get_coaching_advice())
    print("\n--- END OF BRIEFING ---")
