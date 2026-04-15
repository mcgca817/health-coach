-- Health Coach Database Schema
-- PostgreSQL 16

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description)
VALUES (1, 'Initial schema')
ON CONFLICT (version) DO NOTHING;

-- Athlete profile (static or slowly changing data)
CREATE TABLE IF NOT EXISTS athlete_profile (
    id SERIAL PRIMARY KEY,
    height_cm DECIMAL(5,2),
    date_of_birth DATE,
    sex VARCHAR(10),
    ftp INTEGER, -- Functional Threshold Power for cycling
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert default profile
INSERT INTO athlete_profile (height_cm, date_of_birth, sex, ftp)
VALUES (180, '1990-01-01', 'male', 240)
ON CONFLICT DO NOTHING;

-- Goals and phases
CREATE TABLE IF NOT EXISTS goals (
    id SERIAL PRIMARY KEY,
    goal_name VARCHAR(100) NOT NULL, -- e.g., 'recomp_checkpoint', 'race', 'longevity'
    goal_type VARCHAR(50),
    target_date DATE,
    target_weight_kg DECIMAL(5,2),
    notes TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- System phase (what mode the system is in)
CREATE TABLE IF NOT EXISTS system_phase (
    id SERIAL PRIMARY KEY,
    phase VARCHAR(50) NOT NULL, -- 'recomp', 'race_prep', 'longevity'
    start_date DATE NOT NULL,
    end_date DATE,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert default phase
INSERT INTO system_phase (phase, start_date, active)
VALUES ('recomp', CURRENT_DATE, true)
ON CONFLICT DO NOTHING;

-- Rule configuration (editable thresholds)
CREATE TABLE IF NOT EXISTS rule_config (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL UNIQUE,
    rule_value DECIMAL(10,2) NOT NULL,
    rule_unit VARCHAR(20),
    description TEXT,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert default rules
INSERT INTO rule_config (rule_name, rule_value, rule_unit, description) VALUES
('hrv_sigma_threshold', 1.5, 'sigma', 'HRV circuit breaker'),
('rhr_spike_threshold', 7, 'bpm', 'RHR spike circuit breaker'),
('protein_floor_days', 2, 'days', 'Consecutive days below protein floor before trigger'),
('protein_floor_g_per_kg', 1.6, 'g/kg', 'Minimum protein per kg body weight'),
('sleep_debt_hours', 18, 'hours', 'Minimum sleep over 3 days'),
('deficit_cap_kcal', 500, 'kcal', 'Maximum daily calorie deficit'),
('deficit_cap_days', 7, 'days', 'Rolling window for deficit cap'),
('weight_loss_cap_kg_per_week', 0.5, 'kg/week', 'Maximum safe weight loss rate'),
('atl_ctl_ratio_max', 1.5, 'ratio', 'Maximum ATL/CTL ratio')
ON CONFLICT (rule_name) DO NOTHING;

-- Daily biometrics
CREATE TABLE IF NOT EXISTS daily_biometrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    weight_kg DECIMAL(5,2),
    body_fat_pct DECIMAL(4,2),
    hrv INTEGER, -- Heart Rate Variability in ms
    rhr INTEGER, -- Resting Heart Rate in bpm
    sleep_hours DECIMAL(4,2),
    steps INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_biometrics_date ON daily_biometrics (date DESC);

-- Training load (from Intervals.icu)
CREATE TABLE IF NOT EXISTS training_load (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    ctl DECIMAL(6,2), -- Chronic Training Load
    atl DECIMAL(6,2), -- Acute Training Load
    tsb DECIMAL(6,2), -- Training Stress Balance
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_training_load_date ON training_load(date DESC);

-- Workouts (planned and completed)
CREATE TABLE IF NOT EXISTS workouts (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    workout_type VARCHAR(50), -- 'cycling', 'running', 'kettlebell', etc.
    planned BOOLEAN NOT NULL DEFAULT false,
    completed BOOLEAN NOT NULL DEFAULT false,
    tss DECIMAL(6,2), -- Training Stress Score
    intensity_factor DECIMAL(4,3),
    duration_minutes INTEGER,
    workout_description TEXT,
    external_id VARCHAR(100), -- ID from Intervals.icu
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_workouts_date ON workouts (date DESC);

-- Nutrition targets (what we planned)
CREATE TABLE IF NOT EXISTS nutrition_targets (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    kcal_target INTEGER NOT NULL,
    protein_target_g INTEGER NOT NULL,
    carbs_target_g INTEGER NOT NULL,
    fat_target_g INTEGER NOT NULL,
    refeed BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_nutrition_targets_date ON nutrition_targets (date DESC);

-- Nutrition actuals (what actually happened)
CREATE TABLE IF NOT EXISTS nutrition_actuals (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    kcal_actual INTEGER,
    protein_actual_g INTEGER,
    carbs_actual_g INTEGER,
    fat_actual_g INTEGER,
    alcohol_g INTEGER DEFAULT 0,
    meals_count INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_nutrition_actuals_date ON nutrition_actuals (date DESC);

-- Granular Nutrition Logs (from SparkyFitness)
CREATE TABLE IF NOT EXISTS nutrition_logs (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    logged_at TIMESTAMP,
    entry_text TEXT,
    kcal_actual INTEGER,
    protein_actual_g NUMERIC(5,1),
    carbs_actual_g NUMERIC(5,1),
    fat_actual_g NUMERIC(5,1),
    fibre_actual_g NUMERIC(5,1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_nut_logs_date ON nutrition_logs(date DESC);

-- Journal entries
CREATE TABLE IF NOT EXISTS journal_entries (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    entry_text TEXT NOT NULL,
    mood VARCHAR(50),
    stress_level VARCHAR(20),
    summary TEXT, -- AI-generated summary for LLM context
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_journal_date ON journal_entries (date DESC);

-- Daily plans (the output of the Decision Engine)
CREATE TABLE IF NOT EXISTS plans_daily (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    phase VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(3,2),
    plan_json JSONB NOT NULL, -- The full plan structure
    llm_reasoning TEXT,
    hard_constraints_triggered TEXT[],
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_plans_daily_date ON plans_daily (date DESC);

-- Weekly plans/summaries
CREATE TABLE IF NOT EXISTS plans_weekly (
    id SERIAL PRIMARY KEY,
    week_start_date DATE NOT NULL UNIQUE,
    summary_json JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_plans_weekly_date ON plans_weekly (week_start_date DESC);

-- Job run history (for monitoring and healthchecks)
CREATE TABLE IF NOT EXISTS run_history (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    status VARCHAR(20) NOT NULL, -- 'success', 'failure', 'running'
    error_message TEXT,
    records_processed INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_run_history_job ON run_history(job_name, finished_at);
CREATE INDEX IF NOT EXISTS idx_run_history_status ON run_history(status, finished_at);

-- Compliance windows (rolling metrics)
CREATE TABLE IF NOT EXISTS compliance_windows (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    protein_compliance_7d DECIMAL(5,2), -- Percentage of days meeting protein floor
    protein_compliance_14d DECIMAL(5,2),
    protein_compliance_30d DECIMAL(5,2),
    avg_deficit_7d DECIMAL(6,2), -- Average daily deficit in kcal
    avg_deficit_14d DECIMAL(6,2),
    avg_deficit_30d DECIMAL(6,2),
    workout_completion_7d DECIMAL(5,2), -- Percentage of planned workouts completed
    workout_completion_14d DECIMAL(5,2),
    workout_completion_30d DECIMAL(5,2),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_compliance_date ON compliance_windows (date DESC);

-- Workout library (templates)
CREATE TABLE IF NOT EXISTS workout_library (
    id SERIAL PRIMARY KEY,
    workout_name VARCHAR(100) NOT NULL UNIQUE,
    modality VARCHAR(50) NOT NULL, -- 'cycling', 'running', 'kettlebell'
    intensity_zone VARCHAR(20), -- 'z1', 'z2', 'z3', 'z4', 'z5'
    duration_min INTEGER,
    estimated_tss DECIMAL(6,2), -- Intervals.icu format
    workout_text TEXT NOT NULL,
    phases TEXT[], -- Which phases this workout is appropriate for
    notes TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Grant permissions (if needed for specific users)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO healthcoach;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO healthcoach;
