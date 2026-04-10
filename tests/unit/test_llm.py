import pytest
from datetime import date
import sys
import os

# Ensure app is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.decision_engine.llm import format_report

def test_format_report_empty():
    print("\n🔍 Testing: Report generation with ZERO data rows...")
    report = format_report([], [], [], "12:00:00")
    assert report == "No data found."
    print("✅ Verified: Empty report returns correct placeholder string.")

def test_format_report_with_data():
    print("\n🔍 Testing: Full report generation with complex data set...")
    stats = [{
        'date': date(2026, 4, 8),
        'weight_kg': 80.5,
        'weight_ema': 80.6,
        'body_fat_pct': 15.0,
        'sleep_hours': 7.5,
        'hrv': 45,
        'kcal_actual': 2500,
        'kcal_burned': 500,
        'protein_actual_g': 150,
        'carbs_actual_g': 200,
        'fat_actual_g': 80,
        'fibre_actual_g': 30,
        'ctl': 50,
        'atl': 60,
        'tsb': -10
    }]
    training = [{
        'date': date(2026, 4, 8),
        'name': 'Morning Run',
        'distance_km': 5.0,
        'load': 50,
        'average_watts': None
    }]
    journals = [{
        'date': date(2026, 4, 8),
        'mood': 'Good',
        'entry_text': 'Felt great'
    }]
    
    print(f"   -> Input metrics date: {stats[0]['date']}")
    print(f"   -> Input workout: {training[0]['name']}")
    
    report = format_report(stats, training, journals, "12:00:00")
    
    # Assertions with detailed messages
    assert "MCPATTY PERFORMANCE STATUS" in report, "Missing Header"
    assert "**Fitness (CTL):** 50" in report, "CTL Value Incorrect"
    assert "**Fatigue (ATL):** 60" in report, "ATL Value Incorrect"
    assert "**Form (TSB):** -10" in report, "Form Value Incorrect"
    assert "Morning Run" in report, "Workout Name Missing"
    assert "5.0km" in report, "Distance Missing"
    assert "50 Load" in report, "Training Load Missing"
    assert "Felt great" in report, "Journal Entry Missing"
    
    print("✅ Verified: All metrics, workouts, and journals correctly formatted into Markdown.")
    print("-" * 40)
    print("PREVIEW OF GENERATED REPORT:")
    print(report)
    print("-" * 40)
