-- Migration: Add location persistence to profiles
-- Run this in Supabase Dashboard -> SQL Editor

ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS latitude NUMERIC(10, 7),
ADD COLUMN IF NOT EXISTS longitude NUMERIC(10, 7),
ADD COLUMN IF NOT EXISTS location_city TEXT,
ADD COLUMN IF NOT EXISTS location_country TEXT,
ADD COLUMN IF NOT EXISTS location_captured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Enable RLS for these new columns if needed (already enabled for profiles table)
-- Existing policy "Allow all on profiles" covers these columns.
