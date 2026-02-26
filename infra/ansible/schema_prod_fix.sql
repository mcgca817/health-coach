--
-- PostgreSQL database dump
--

\restrict Log7IhYRYx66M2PkfJZsbKKDiM0Exm1fvxiyxVaw54f14dcjXXUe4iSYwxRXcDv

-- Dumped from database version 16.11 (Debian 16.11-1.pgdg13+1)
-- Dumped by pg_dump version 16.11 (Debian 16.11-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: activities; Type: TABLE; Schema: public; Owner: healthcoach
--

CREATE TABLE public.activities (
    id text NOT NULL,
    date date NOT NULL,
    name text,
    type text,
    distance_km numeric(6,2),
    moving_time_min numeric(6,2),
    load integer,
    average_watts integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.activities OWNER TO healthcoach;

--
-- Name: athlete_profile; Type: TABLE; Schema: public; Owner: healthcoach
--

CREATE TABLE public.athlete_profile (
    id integer NOT NULL,
    height_cm numeric(5,2),
    date_of_birth date,
    sex character varying(10),
    ftp integer,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.athlete_profile OWNER TO healthcoach;

--
-- Name: athlete_profile_id_seq; Type: SEQUENCE; Schema: public; Owner: healthcoach
--

CREATE SEQUENCE public.athlete_profile_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.athlete_profile_id_seq OWNER TO healthcoach;

--
-- Name: athlete_profile_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: healthcoach
--

ALTER SEQUENCE public.athlete_profile_id_seq OWNED BY public.athlete_profile.id;


--
-- Name: compliance_windows; Type: TABLE; Schema: public; Owner: healthcoach
--

CREATE TABLE public.compliance_windows (
    id integer NOT NULL,
    date date NOT NULL,
    protein_compliance_7d numeric(5,2),
    protein_compliance_14d numeric(5,2),
    protein_compliance_30d numeric(5,2),
    avg_deficit_7d numeric(6,2),
    avg_deficit_14d numeric(6,2),
    avg_deficit_30d numeric(6,2),
    workout_completion_7d numeric(5,2),
    workout_completion_14d numeric(5,2),
    workout_completion_30d numeric(5,2),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.compliance_windows OWNER TO healthcoach;

--
-- Name: compliance_windows_id_seq; Type: SEQUENCE; Schema: public; Owner: healthcoach
--

CREATE SEQUENCE public.compliance_windows_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.compliance_windows_id_seq OWNER TO healthcoach;

--
-- Name: compliance_windows_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: healthcoach
--

ALTER SEQUENCE public.compliance_windows_id_seq OWNED BY public.compliance_windows.id;


--
-- Name: daily_biometrics; Type: TABLE; Schema: public; Owner: healthcoach
--

CREATE TABLE public.daily_biometrics (
    id integer NOT NULL,
    date date NOT NULL,
    weight_kg numeric(5,2),
    body_fat_pct numeric(4,2),
    hrv integer,
    rhr integer,
    sleep_hours numeric(4,2),
    steps integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ctl integer,
    atl integer,
    tsb integer,
    resting_hr integer,
    kcal_burned integer
);


ALTER TABLE public.daily_biometrics OWNER TO healthcoach;

--
-- Name: daily_biometrics_id_seq; Type: SEQUENCE; Schema: public; Owner: healthcoach
--

CREATE SEQUENCE public.daily_biometrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.daily_biometrics_id_seq OWNER TO healthcoach;

--
-- Name: daily_biometrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: healthcoach
--

ALTER SEQUENCE public.daily_biometrics_id_seq OWNED BY public.daily_biometrics.id;


--
-- Name: goals; Type: TABLE; Schema: public; Owner: healthcoach
--

CREATE TABLE public.goals (
    id integer NOT NULL,
    goal_name character varying(100) NOT NULL,
    goal_type character varying(50),
    target_date date,
    target_weight_kg numeric(5,2),
    notes text,
    active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.goals OWNER TO healthcoach;

--
-- Name: goals_id_seq; Type: SEQUENCE; Schema: public; Owner: healthcoach
--

CREATE SEQUENCE public.goals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.goals_id_seq OWNER TO healthcoach;

--
-- Name: goals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: healthcoach
--

ALTER SEQUENCE public.goals_id_seq OWNED BY public.goals.id;


--
-- Name: journal_entries; Type: TABLE; Schema: public; Owner: healthcoach
--

CREATE TABLE public.journal_entries (
    id integer NOT NULL,
    date date NOT NULL,
    entry_text text NOT NULL,
    mood character varying(50),
    stress_level character varying(20),
    summary text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.journal_entries OWNER TO healthcoach;

--
-- Name: journal_entries_id_seq; Type: SEQUENCE; Schema: public; Owner: healthcoach
--

CREATE SEQUENCE public.journal_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.journal_entries_id_seq OWNER TO healthcoach;

--
-- Name: journal_entries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: healthcoach
--

ALTER SEQUENCE public.journal_entries_id_seq OWNED BY public.journal_entries.id;


--
-- Name: nutrition_actuals; Type: TABLE; Schema: public; Owner: healthcoach
--

CREATE TABLE public.nutrition_actuals (
    id integer NOT NULL,
    date date NOT NULL,
    kcal_actual integer,
    protein_actual_g integer,
    carbs_actual_g integer,
    fat_actual_g integer,
    alcohol_g integer DEFAULT 0,
    meals_count integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.nutrition_actuals OWNER TO healthcoach;

--
-- Name: nutrition_actuals_id_seq; Type: SEQUENCE; Schema: public; Owner: healthcoach
--

CREATE SEQUENCE public.nutrition_actuals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.nutrition_actuals_id_seq OWNER TO healthcoach;

--
-- Name: nutrition_actuals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: healthcoach
--

ALTER SEQUENCE public.nutrition_actuals_id_seq OWNED BY public.nutrition_actuals.id;


--
-- Name: nutrition_logs; Type: TABLE; Schema: public; Owner: healthcoach
--

CREATE TABLE public.nutrition_logs (
    id integer NOT NULL,
    date date NOT NULL,
    entry_text text,
    kcal_actual integer,
    protein_actual_g numeric(5,1),
    carbs_actual_g numeric(5,1),
    fat_actual_g numeric(5,1),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.nutrition_logs OWNER TO healthcoach;

--
-- Name: nutrition_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: healthcoach
--

CREATE SEQUENCE public.nutrition_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.nutrition_logs_id_seq OWNER TO healthcoach;

--
-- Name: nutrition_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: healthcoach
--

ALTER SEQUENCE public.nutrition_logs_id_seq OWNED BY public.nutrition_logs.id;


--
-- Name: nutrition_targets; Type: TABLE; Schema: public; Owner: healthcoach
--

CREATE TABLE public.nutrition_targets (
    id integer NOT NULL,
    date date NOT NULL,
    kcal_target integer NOT NULL,
    protein_target_g integer NOT NULL,
    carbs_target_g integer NOT NULL,
    fat_target_g integer NOT NULL,
    refeed boolean DEFAULT false,
    notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.nutrition_targets OWNER TO healthcoach;

--
-- Name: nutrition_targets_id_seq; Type: SEQUENCE; Schema: public; Owner: healthcoach
--

CREATE SEQUENCE public.nutrition_targets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.nutrition_targets_id_seq OWNER TO healthcoach;

--
-- Name: nutrition_targets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: healthcoach
--

ALTER SEQUENCE public.nutrition_targets_id_seq OWNED BY public.nutrition_targets.id;


--
-- Name: plans_daily; Type: TABLE; Schema: public; Owner: healthcoach
--

CREATE TABLE public.plans_daily (
    id integer NOT NULL,
    date date NOT NULL,
    phase character varying(50) NOT NULL,
    confidence_score numeric(3,2),
    plan_json jsonb NOT NULL,
    llm_reasoning text,
    hard_constraints_triggered text[],
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.plans_daily OWNER TO healthcoach;

--
-- Name: plans_daily_id_seq; Type: SEQUENCE; Schema: public; Owner: healthcoach
--

CREATE SEQUENCE public.plans_daily_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.plans_daily_id_seq OWNER TO healthcoach;

--
-- Name: plans_daily_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: healthcoach
--

ALTER SEQUENCE public.plans_daily_id_seq OWNED BY public.plans_daily.id;


--
-- Name: plans_weekly; Type: TABLE; Schema: public; Owner: healthcoach
--

CREATE TABLE public.plans_weekly (
    id integer NOT NULL,
    week_start_date date NOT NULL,
    summary_json jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.plans_weekly OWNER TO healthcoach;

--
-- Name: plans_weekly_id_seq; Type: SEQUENCE; Schema: public; Owner: healthcoach
--

CREATE SEQUENCE public.plans_weekly_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.plans_weekly_id_seq OWNER TO healthcoach;

--
-- Name: plans_weekly_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: healthcoach
--

ALTER SEQUENCE public.plans_weekly_id_seq OWNED BY public.plans_weekly.id;


--
-- Name: rule_config; Type: TABLE; Schema: public; Owner: healthcoach
--

CREATE TABLE public.rule_config (
    id integer NOT NULL,
    rule_name character varying(100) NOT NULL,
    rule_value numeric(10,2) NOT NULL,
    rule_unit character varying(20),
    description text,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.rule_config OWNER TO healthcoach;

--
-- Name: rule_config_id_seq; Type: SEQUENCE; Schema: public; Owner: healthcoach
--

CREATE SEQUENCE public.rule_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rule_config_id_seq OWNER TO healthcoach;

--
-- Name: rule_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: healthcoach
--

ALTER SEQUENCE public.rule_config_id_seq OWNED BY public.rule_config.id;


--
-- Name: run_history; Type: TABLE; Schema: public; Owner: healthcoach
--

CREATE TABLE public.run_history (
    id integer NOT NULL,
    job_name character varying(100) NOT NULL,
    started_at timestamp without time zone NOT NULL,
    finished_at timestamp without time zone,
    status character varying(20) NOT NULL,
    error_message text,
    records_processed integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.run_history OWNER TO healthcoach;

--
-- Name: run_history_id_seq; Type: SEQUENCE; Schema: public; Owner: healthcoach
--

CREATE SEQUENCE public.run_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.run_history_id_seq OWNER TO healthcoach;

--
-- Name: run_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: healthcoach
--

ALTER SEQUENCE public.run_history_id_seq OWNED BY public.run_history.id;


--
-- Name: schema_version; Type: TABLE; Schema: public; Owner: healthcoach
--

CREATE TABLE public.schema_version (
    version integer NOT NULL,
    applied_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    description text
);


ALTER TABLE public.schema_version OWNER TO healthcoach;

--
-- Name: system_phase; Type: TABLE; Schema: public; Owner: healthcoach
--

CREATE TABLE public.system_phase (
    id integer NOT NULL,
    phase character varying(50) NOT NULL,
    start_date date NOT NULL,
    end_date date,
    active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.system_phase OWNER TO healthcoach;

--
-- Name: system_phase_id_seq; Type: SEQUENCE; Schema: public; Owner: healthcoach
--

CREATE SEQUENCE public.system_phase_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_phase_id_seq OWNER TO healthcoach;

--
-- Name: system_phase_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: healthcoach
--

ALTER SEQUENCE public.system_phase_id_seq OWNED BY public.system_phase.id;


--
-- Name: training_load; Type: TABLE; Schema: public; Owner: healthcoach
--

CREATE TABLE public.training_load (
    id integer NOT NULL,
    date date NOT NULL,
    ctl numeric(6,2),
    atl numeric(6,2),
    tsb numeric(6,2),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.training_load OWNER TO healthcoach;

--
-- Name: training_load_id_seq; Type: SEQUENCE; Schema: public; Owner: healthcoach
--

CREATE SEQUENCE public.training_load_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.training_load_id_seq OWNER TO healthcoach;

--
-- Name: training_load_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: healthcoach
--

ALTER SEQUENCE public.training_load_id_seq OWNED BY public.training_load.id;


--
-- Name: workout_library; Type: TABLE; Schema: public; Owner: healthcoach
--

CREATE TABLE public.workout_library (
    id integer NOT NULL,
    workout_name character varying(100) NOT NULL,
    modality character varying(50) NOT NULL,
    intensity_zone character varying(20),
    duration_min integer,
    estimated_tss numeric(6,2),
    workout_text text NOT NULL,
    phases text[],
    notes text,
    active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.workout_library OWNER TO healthcoach;

--
-- Name: workout_library_id_seq; Type: SEQUENCE; Schema: public; Owner: healthcoach
--

CREATE SEQUENCE public.workout_library_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workout_library_id_seq OWNER TO healthcoach;

--
-- Name: workout_library_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: healthcoach
--

ALTER SEQUENCE public.workout_library_id_seq OWNED BY public.workout_library.id;


--
-- Name: workouts; Type: TABLE; Schema: public; Owner: healthcoach
--

CREATE TABLE public.workouts (
    id integer NOT NULL,
    date date NOT NULL,
    workout_type character varying(50),
    planned boolean DEFAULT false NOT NULL,
    completed boolean DEFAULT false NOT NULL,
    tss numeric(6,2),
    intensity_factor numeric(4,3),
    duration_minutes integer,
    workout_description text,
    external_id character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at timestamp without time zone
);


ALTER TABLE public.workouts OWNER TO healthcoach;

--
-- Name: workouts_id_seq; Type: SEQUENCE; Schema: public; Owner: healthcoach
--

CREATE SEQUENCE public.workouts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workouts_id_seq OWNER TO healthcoach;

--
-- Name: workouts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: healthcoach
--

ALTER SEQUENCE public.workouts_id_seq OWNED BY public.workouts.id;


--
-- Name: athlete_profile id; Type: DEFAULT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.athlete_profile ALTER COLUMN id SET DEFAULT nextval('public.athlete_profile_id_seq'::regclass);


--
-- Name: compliance_windows id; Type: DEFAULT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.compliance_windows ALTER COLUMN id SET DEFAULT nextval('public.compliance_windows_id_seq'::regclass);


--
-- Name: daily_biometrics id; Type: DEFAULT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.daily_biometrics ALTER COLUMN id SET DEFAULT nextval('public.daily_biometrics_id_seq'::regclass);


--
-- Name: goals id; Type: DEFAULT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.goals ALTER COLUMN id SET DEFAULT nextval('public.goals_id_seq'::regclass);


--
-- Name: journal_entries id; Type: DEFAULT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.journal_entries ALTER COLUMN id SET DEFAULT nextval('public.journal_entries_id_seq'::regclass);


--
-- Name: nutrition_actuals id; Type: DEFAULT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.nutrition_actuals ALTER COLUMN id SET DEFAULT nextval('public.nutrition_actuals_id_seq'::regclass);


--
-- Name: nutrition_logs id; Type: DEFAULT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.nutrition_logs ALTER COLUMN id SET DEFAULT nextval('public.nutrition_logs_id_seq'::regclass);


--
-- Name: nutrition_targets id; Type: DEFAULT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.nutrition_targets ALTER COLUMN id SET DEFAULT nextval('public.nutrition_targets_id_seq'::regclass);


--
-- Name: plans_daily id; Type: DEFAULT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.plans_daily ALTER COLUMN id SET DEFAULT nextval('public.plans_daily_id_seq'::regclass);


--
-- Name: plans_weekly id; Type: DEFAULT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.plans_weekly ALTER COLUMN id SET DEFAULT nextval('public.plans_weekly_id_seq'::regclass);


--
-- Name: rule_config id; Type: DEFAULT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.rule_config ALTER COLUMN id SET DEFAULT nextval('public.rule_config_id_seq'::regclass);


--
-- Name: run_history id; Type: DEFAULT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.run_history ALTER COLUMN id SET DEFAULT nextval('public.run_history_id_seq'::regclass);


--
-- Name: system_phase id; Type: DEFAULT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.system_phase ALTER COLUMN id SET DEFAULT nextval('public.system_phase_id_seq'::regclass);


--
-- Name: training_load id; Type: DEFAULT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.training_load ALTER COLUMN id SET DEFAULT nextval('public.training_load_id_seq'::regclass);


--
-- Name: workout_library id; Type: DEFAULT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.workout_library ALTER COLUMN id SET DEFAULT nextval('public.workout_library_id_seq'::regclass);


--
-- Name: workouts id; Type: DEFAULT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.workouts ALTER COLUMN id SET DEFAULT nextval('public.workouts_id_seq'::regclass);


--
-- Name: activities activities_pkey; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.activities
    ADD CONSTRAINT activities_pkey PRIMARY KEY (id);


--
-- Name: athlete_profile athlete_profile_pkey; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.athlete_profile
    ADD CONSTRAINT athlete_profile_pkey PRIMARY KEY (id);


--
-- Name: compliance_windows compliance_windows_date_key; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.compliance_windows
    ADD CONSTRAINT compliance_windows_date_key UNIQUE (date);


--
-- Name: compliance_windows compliance_windows_pkey; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.compliance_windows
    ADD CONSTRAINT compliance_windows_pkey PRIMARY KEY (id);


--
-- Name: daily_biometrics daily_biometrics_date_key; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.daily_biometrics
    ADD CONSTRAINT daily_biometrics_date_key UNIQUE (date);


--
-- Name: daily_biometrics daily_biometrics_pkey; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.daily_biometrics
    ADD CONSTRAINT daily_biometrics_pkey PRIMARY KEY (id);


--
-- Name: goals goals_pkey; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.goals
    ADD CONSTRAINT goals_pkey PRIMARY KEY (id);


--
-- Name: journal_entries journal_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.journal_entries
    ADD CONSTRAINT journal_entries_pkey PRIMARY KEY (id);


--
-- Name: nutrition_actuals nutrition_actuals_date_key; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.nutrition_actuals
    ADD CONSTRAINT nutrition_actuals_date_key UNIQUE (date);


--
-- Name: nutrition_actuals nutrition_actuals_pkey; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.nutrition_actuals
    ADD CONSTRAINT nutrition_actuals_pkey PRIMARY KEY (id);


--
-- Name: nutrition_logs nutrition_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.nutrition_logs
    ADD CONSTRAINT nutrition_logs_pkey PRIMARY KEY (id);


--
-- Name: nutrition_targets nutrition_targets_date_key; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.nutrition_targets
    ADD CONSTRAINT nutrition_targets_date_key UNIQUE (date);


--
-- Name: nutrition_targets nutrition_targets_pkey; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.nutrition_targets
    ADD CONSTRAINT nutrition_targets_pkey PRIMARY KEY (id);


--
-- Name: plans_daily plans_daily_date_key; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.plans_daily
    ADD CONSTRAINT plans_daily_date_key UNIQUE (date);


--
-- Name: plans_daily plans_daily_pkey; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.plans_daily
    ADD CONSTRAINT plans_daily_pkey PRIMARY KEY (id);


--
-- Name: plans_weekly plans_weekly_pkey; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.plans_weekly
    ADD CONSTRAINT plans_weekly_pkey PRIMARY KEY (id);


--
-- Name: plans_weekly plans_weekly_week_start_date_key; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.plans_weekly
    ADD CONSTRAINT plans_weekly_week_start_date_key UNIQUE (week_start_date);


--
-- Name: rule_config rule_config_pkey; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.rule_config
    ADD CONSTRAINT rule_config_pkey PRIMARY KEY (id);


--
-- Name: rule_config rule_config_rule_name_key; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.rule_config
    ADD CONSTRAINT rule_config_rule_name_key UNIQUE (rule_name);


--
-- Name: run_history run_history_pkey; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.run_history
    ADD CONSTRAINT run_history_pkey PRIMARY KEY (id);


--
-- Name: schema_version schema_version_pkey; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.schema_version
    ADD CONSTRAINT schema_version_pkey PRIMARY KEY (version);


--
-- Name: system_phase system_phase_pkey; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.system_phase
    ADD CONSTRAINT system_phase_pkey PRIMARY KEY (id);


--
-- Name: training_load training_load_date_key; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.training_load
    ADD CONSTRAINT training_load_date_key UNIQUE (date);


--
-- Name: training_load training_load_pkey; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.training_load
    ADD CONSTRAINT training_load_pkey PRIMARY KEY (id);


--
-- Name: workout_library workout_library_pkey; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.workout_library
    ADD CONSTRAINT workout_library_pkey PRIMARY KEY (id);


--
-- Name: workout_library workout_library_workout_name_key; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.workout_library
    ADD CONSTRAINT workout_library_workout_name_key UNIQUE (workout_name);


--
-- Name: workouts workouts_pkey; Type: CONSTRAINT; Schema: public; Owner: healthcoach
--

ALTER TABLE ONLY public.workouts
    ADD CONSTRAINT workouts_pkey PRIMARY KEY (id);


--
-- Name: idx_activities_date; Type: INDEX; Schema: public; Owner: healthcoach
--

CREATE INDEX idx_activities_date ON public.activities USING btree (date DESC);


--
-- Name: idx_biometrics_date; Type: INDEX; Schema: public; Owner: healthcoach
--

CREATE INDEX idx_biometrics_date ON public.daily_biometrics USING btree (date DESC);


--
-- Name: idx_compliance_date; Type: INDEX; Schema: public; Owner: healthcoach
--

CREATE INDEX idx_compliance_date ON public.compliance_windows USING btree (date DESC);


--
-- Name: idx_journal_date; Type: INDEX; Schema: public; Owner: healthcoach
--

CREATE INDEX idx_journal_date ON public.journal_entries USING btree (date DESC);


--
-- Name: idx_nut_logs_date; Type: INDEX; Schema: public; Owner: healthcoach
--

CREATE INDEX idx_nut_logs_date ON public.nutrition_logs USING btree (date DESC);


--
-- Name: idx_nutrition_actuals_date; Type: INDEX; Schema: public; Owner: healthcoach
--

CREATE INDEX idx_nutrition_actuals_date ON public.nutrition_actuals USING btree (date DESC);


--
-- Name: idx_nutrition_targets_date; Type: INDEX; Schema: public; Owner: healthcoach
--

CREATE INDEX idx_nutrition_targets_date ON public.nutrition_targets USING btree (date DESC);


--
-- Name: idx_plans_daily_date; Type: INDEX; Schema: public; Owner: healthcoach
--

CREATE INDEX idx_plans_daily_date ON public.plans_daily USING btree (date DESC);


--
-- Name: idx_plans_weekly_date; Type: INDEX; Schema: public; Owner: healthcoach
--

CREATE INDEX idx_plans_weekly_date ON public.plans_weekly USING btree (week_start_date DESC);


--
-- Name: idx_run_history_job; Type: INDEX; Schema: public; Owner: healthcoach
--

CREATE INDEX idx_run_history_job ON public.run_history USING btree (job_name, finished_at);


--
-- Name: idx_run_history_status; Type: INDEX; Schema: public; Owner: healthcoach
--

CREATE INDEX idx_run_history_status ON public.run_history USING btree (status, finished_at);


--
-- Name: idx_training_load_date; Type: INDEX; Schema: public; Owner: healthcoach
--

CREATE INDEX idx_training_load_date ON public.training_load USING btree (date DESC);


--
-- Name: idx_workouts_date; Type: INDEX; Schema: public; Owner: healthcoach
--

CREATE INDEX idx_workouts_date ON public.workouts USING btree (date DESC);


--
-- PostgreSQL database dump complete
--

\unrestrict Log7IhYRYx66M2PkfJZsbKKDiM0Exm1fvxiyxVaw54f14dcjXXUe4iSYwxRXcDv

