"""
Risk Engine Service — Orchestrates the full risk prediction flow.
Combines user data from Supabase with AI prediction via Groq.
Migrated from neurofit_risk_engine14/app.py business logic.
"""
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from supabase import create_client, Client
from app.config import settings
from app.services.gemini_helper import call_gemini
from app.services.prompt_builder import build_prompt


def _get_supabase() -> Optional[Client]:
    """Get Supabase client with error handling."""
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    if not url or not key:
        print("[WARN] Supabase not configured (SUPABASE_URL / SUPABASE_KEY missing)")
        return None
    try:
        # Check if URL is valid before creating client
        return create_client(url, key)
    except Exception as e:
        print(f"[WARN] Failed to initialize Supabase client: {e}")
        return None


def get_profile(email: str) -> Optional[dict]:
    """Get user profile from Supabase using email."""
    sb = _get_supabase()
    if not sb:
        return None
    try:
        response = sb.table("profiles").select("*").eq("email", email).limit(1).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[ERROR] Supabase profile fetch error: {e}")
        return None


def update_user_profile(email: str, profile_data: dict) -> bool:
    """Update user profile in Supabase using email."""
    sb = _get_supabase()
    if not sb:
        return False
    try:
        result = sb.table("profiles").update(profile_data).eq("email", email).execute()
        return bool(result.data)
    except Exception as e:
        print(f"[ERROR] Profile update failed: {e}")
        return False


def save_daily_log(email: str, log_data: dict) -> tuple:
    """Save or update a daily log entry using user_email."""
    sb = _get_supabase()
    if not sb:
        return False, "Supabase not configured"
    try:
        db_data = {
            "log_date":         log_data["date"],
            "breakfast":        log_data.get("breakfast") or None,
            "lunch":            log_data.get("lunch") or None,
            "snacks":           log_data.get("snacks") or None,
            "dinner":           log_data.get("dinner") or None,
            "water_liters":     log_data.get("water_liters"),
            "exercise_minutes": log_data.get("exercise_minutes"),
            "sleep_hours":      log_data.get("sleep_hours"),
            "symptoms":         log_data.get("symptoms") or None,
            "steps_today":      int(log_data["steps_today"]) if log_data.get("steps_today") else None,
            "calories_today":   float(log_data["calories_today"]) if log_data.get("calories_today") else None,
        }
        existing = sb.table("daily_logs").select("id").eq("user_email", email).eq("log_date", log_data["date"]).execute()
        if existing.data:
            result = sb.table("daily_logs").update(db_data).eq("id", existing.data[0]["id"]).execute()
        else:
            db_data["user_email"] = email
            result = sb.table("daily_logs").insert(db_data).execute()
        if result.data:
            return True, None
        return False, "Supabase returned no data"
    except Exception as e:
        return False, str(e)


def save_medical_history(email: str, history_data: dict) -> tuple:
    """Save a medical history record using user_email."""
    sb = _get_supabase()
    if not sb:
        return False, "Supabase not configured"
    try:
        history_data["user_email"] = email
        result = sb.table("medical_history").insert(history_data).execute()
        if result.data:
            return True, None
        return False, "Supabase returned no data"
    except Exception as e:
        return False, str(e)


def load_user_history(email: str, days: int = 30) -> dict:
    """Load user's daily logs, medical history, vitals, symptom history, and recent predictions from Supabase."""
    sb = _get_supabase()
    default_history = {
        "daily_logs": [], 
        "medical_history": [], 
        "recent_predictions": [], 
        "vitals": [], 
        "symptom_history": [], 
        "profile_snapshot": {}
    }
    
    if not sb:
        print("[INFO] Supabase not available, returning empty history for fallback mode.")
        return default_history
        
    try:
        since = (datetime.now() - timedelta(days=days)).date().isoformat()
        
        # 1. Fetch User Profile Snapshot
        u_res = sb.table("profiles").select("*").eq("email", email).limit(1).execute()
        profile_snapshot = u_res.data[0] if u_res.data else {}

        # 2. Daily logs
        logs = sb.table("daily_logs").select("*").eq("user_email", email).gte("log_date", since).order("log_date", desc=True).execute()
        
        # 3. Medical history
        medical = sb.table("medical_history").select("*").eq("user_email", email).order("created_at", desc=True).limit(20).execute()
        
        # 4. Recent predictions
        predictions = sb.table("risk_predictions").select("*").eq("user_email", email).order("prediction_date", desc=True).limit(10).execute()
        
        # 5. Vitals from 'user_vitals' table
        v_res = sb.table("user_vitals").select("*").eq("user_email", email).order("recorded_at", desc=True).limit(30).execute()
        vitals_data = v_res.data or []
            
        # 6. Symptoms analysis history (records link through medical_forms)
        symptom_res = []
        f_res = sb.table("medical_forms").select("formid").eq("user_email", email).order("updated_at", desc=True).limit(1).execute()
        if f_res.data:
            form_id = f_res.data[0]["formid"]
            s_res = sb.table("records").select("*").eq("form_id", form_id).order("recorded_at", desc=True).limit(10).execute()
            symptom_res = s_res.data or []

        return {
            "profile_snapshot": profile_snapshot,
            "daily_logs": logs.data or [],
            "medical_history": medical.data or [],
            "recent_predictions": predictions.data or [],
            "vitals": vitals_data,
            "symptom_history": symptom_res
        }
    except Exception as e:
        print(f"[ERROR] Error loading history from Supabase: {e}")
        return default_history


def save_risk_prediction(user_id: str, prediction_data: dict) -> tuple:
    """Save a risk prediction result."""
    sb = _get_supabase()
    if not sb:
        return False, "Supabase not configured"
    try:
        prediction_data["user_id"] = user_id
        result = sb.table("risk_predictions").insert(prediction_data).execute()
        if result.data:
            return True, None
        return False, "Supabase returned no data"
    except Exception as e:
        return False, str(e)


def run_risk_prediction(user_id: str, user_data: dict) -> dict:
    """
    Run the full risk prediction pipeline:
    1. Build prompt from user data
    2. Call Groq AI
    3. Save prediction to Supabase
    4. Return result
    """
    # Build prompt
    prompt = build_prompt(user_data)

    # Call AI
    result = call_gemini(prompt)

    # Save to Supabase if successful
    if result.get("risk_level") != "Error":
        prediction_record = {
            "prediction_date": datetime.now().isoformat(),
            "risk_level": result.get("risk_level", "Unknown"),
            "risk_percentages": result.get("risk_percentages", {}),
            "trend_prediction": result.get("trend_prediction", {}),
            "recommendations": result.get("recommendations", []),
            "key_reasons": result.get("key_reasons", []),
        }
        save_risk_prediction(user_id, prediction_record)

    return result
