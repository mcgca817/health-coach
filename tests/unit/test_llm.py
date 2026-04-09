import pytest
from datetime import date
import sys
import os

# Ensure app is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.decision_engine.llm import format_report

def test_format_report_empty():
    report = format_report([], [], [], "12:00:00")
    assert report == "No data found."

def test_format_report_with_data():
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
    
    report = format_report(stats, training, journals, "12:00:00")
    
    assert "MCPATTY PERFORMANCE STATUS" in report
    assert "Fitness (CTL): 50" in report
    assert "Fatigue (ATL): 60" in report
    assert "Form (TSB): -10" in report
    assert "Morning Run" in report
    assert "5.0km" in report
    assert "50 Load" in report
    assert "Felt great" in report
