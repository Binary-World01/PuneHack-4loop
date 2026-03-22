-- ================================================================
-- NeuroFit Database Schema
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- ================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ================================================================
-- TABLES
-- ================================================================

-- Profiles Table (Extends Supabase Auth)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  age INTEGER CHECK (age > 0 AND age < 120),
  gender TEXT CHECK (gender IN ('male', 'female', 'other')),
  height_cm NUMERIC(5,2) CHECK (height_cm > 0),
  weight_kg NUMERIC(5,2) CHECK (weight_kg > 0),
  existing_conditions TEXT[] DEFAULT ARRAY[]::TEXT[],
  family_history TEXT[] DEFAULT ARRAY[]::TEXT[],
  avatar_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Daily Logs
CREATE TABLE IF NOT EXISTS daily_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  log_date DATE NOT NULL,
  breakfast TEXT,
  lunch TEXT,
  snacks TEXT,
  dinner TEXT,
  water_liters NUMERIC(3,1) CHECK (water_liters >= 0),
  exercise_minutes INTEGER CHECK (exercise_minutes >= 0),
  sleep_hours NUMERIC(3,1) CHECK (sleep_hours >= 0 AND sleep_hours <= 24),
  symptoms TEXT,
  steps_today INTEGER CHECK (steps_today >= 0),
  calories_today NUMERIC(6,1) CHECK (calories_today >= 0),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, log_date)
);

-- Medical History
CREATE TABLE IF NOT EXISTS medical_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  illness_description TEXT NOT NULL,
  illness_date DATE,
  prescription_text TEXT,
  prescription_image_url TEXT,   -- stores Supabase Storage public URL
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Medical Forms (Detailed form snapshots)
CREATE TABLE IF NOT EXISTS medical_forms (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  form_type TEXT NOT NULL, -- e.g., 'onboarding', 'general_checkup'
  form_data JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Emergency Contacts
CREATE TABLE IF NOT EXISTS emergency_contacts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  contact_name TEXT NOT NULL,
  relationship TEXT,
  phone_number TEXT NOT NULL,
  email TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User Vitals (Real-time and manual streams)
CREATE TABLE IF NOT EXISTS user_vitals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  heart_rate INTEGER,
  blood_pressure_sys INTEGER,
  blood_pressure_dia INTEGER,
  blood_oxygen NUMERIC(5,2),
  temperature NUMERIC(5,2),
  steps INTEGER,
  sleep_hours NUMERIC(3,1),
  source TEXT DEFAULT 'manual', -- 'wearable', 'manual'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Records (Symptom Analysis & Clinical Assessments)
CREATE TABLE IF NOT EXISTS records (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  record_type TEXT DEFAULT 'symptom_analysis',
  symptoms TEXT[],
  diagnosis TEXT,
  confidence_score NUMERIC(5,2),
  report_data JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Admin / Outbreak Tracking
CREATE TABLE IF NOT EXISTS admin (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  patient_id UUID REFERENCES records(id) ON DELETE CASCADE,
  latitude NUMERIC(10, 7),
  longitude NUMERIC(10, 7),
  location_city TEXT,
  location_region TEXT,
  location_country TEXT,
  disease_category TEXT, -- 'flu_like', 'neuro', etc.
  spreadable BOOLEAN DEFAULT FALSE,
  disease_type TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Risk Predictions
CREATE TABLE IF NOT EXISTS risk_predictions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  prediction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  risk_level TEXT CHECK (risk_level IN ('Low', 'Moderate', 'High', 'Unknown', 'Error')),
  risk_percentages JSONB NOT NULL,
  trend_prediction JSONB,
  recommendations TEXT[],
  key_reasons TEXT[],
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Google Fit Tokens
CREATE TABLE IF NOT EXISTS google_fit_tokens (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  access_token TEXT,
  refresh_token TEXT,
  token_expiry TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ================================================================
-- ROW LEVEL SECURITY
-- ================================================================
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_forms ENABLE ROW LEVEL SECURITY;
ALTER TABLE emergency_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_vitals ENABLE ROW LEVEL SECURITY;
ALTER TABLE records ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE google_fit_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin ENABLE ROW LEVEL SECURITY;

-- ----------------------------------------------------------------
-- POLICIES (Allow All for Hackathon Simplicity, can be refined for production)
-- ----------------------------------------------------------------
CREATE POLICY "Allow all on profiles" ON profiles FOR ALL USING (true);
CREATE POLICY "Allow all on daily_logs" ON daily_logs FOR ALL USING (true);
CREATE POLICY "Allow all on medical_history" ON medical_history FOR ALL USING (true);
CREATE POLICY "Allow all on medical_forms" ON medical_forms FOR ALL USING (true);
CREATE POLICY "Allow all on emergency_contacts" ON emergency_contacts FOR ALL USING (true);
CREATE POLICY "Allow all on user_vitals" ON user_vitals FOR ALL USING (true);
CREATE POLICY "Allow all on records" ON records FOR ALL USING (true);
CREATE POLICY "Allow all on risk_predictions" ON risk_predictions FOR ALL USING (true);
CREATE POLICY "Allow all on google_fit_tokens" ON google_fit_tokens FOR ALL USING (true);
CREATE POLICY "Allow all on admin" ON admin FOR ALL USING (true);


-- ================================================================
-- STORAGE BUCKET SETUP
-- ================================================================
-- Bucket name : prescriptions
-- Public      : YES
tions');