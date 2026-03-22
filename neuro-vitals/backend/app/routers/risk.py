"""
Risk Prediction Router — FastAPI endpoints for the risk engine.
Exposes the NeuroFit Risk Prediction Engine via REST API.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.risk_engine import (
    get_profile,
    update_user_profile,
    save_daily_log,
    save_medical_history,
    load_user_history,
    run_risk_prediction,
)
from app.services.ocr_helper import extract_text_from_image

router = APIRouter(prefix="/risk", tags=["Risk Engine"])


# ─── Request / Response Models ────────────────────────────────────

class UserProfile(BaseModel):
    email: str = "default@neurovitals.local"
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    existing_conditions: Optional[List[str]] = Field(default_factory=list)
    family_history: Optional[List[str]] = Field(default_factory=list)


class DailyLogInput(BaseModel):
    date: str
    breakfast: Optional[str] = None
    lunch: Optional[str] = None
    snacks: Optional[str] = None
    dinner: Optional[str] = None
    water_liters: Optional[float] = 1.5
    exercise_minutes: Optional[int] = 0
    sleep_hours: Optional[float] = 7.0
    symptoms: Optional[str] = None
    steps_today: Optional[int] = 0
    calories_today: Optional[float] = 0.0


class MedicalRecordInput(BaseModel):
    illness_description: str
    illness_date: Optional[str] = None
    prescription_text: Optional[str] = None


class RiskPredictionRequest(BaseModel):
    """Full request for risk prediction — profile + logs + medical records."""
    profile: UserProfile
    daily_log: Optional[DailyLogInput] = None
    medical_records: Optional[List[MedicalRecordInput]] = Field(default_factory=list)


# ─── Endpoints ────────────────────────────────────────────────────

@router.post("/predict")
async def predict_risk(request: RiskPredictionRequest):
    """
    Run full medical risk prediction.
    Accepts user profile, daily log, and medical records.
    Returns AI-generated risk assessment with scores, reasoning, and recommendations.
    """
    try:
        user_email = request.profile.email
        user = get_profile(user_email)

        # Update profile if DB is available
        if user_email != "fallback_id":
            profile_update = {}
            if request.profile.age: profile_update["age"] = request.profile.age
            if request.profile.gender: profile_update["gender"] = request.profile.gender
            # Map full_name to name
            if request.profile.full_name: profile_update["name"] = request.profile.full_name
            
            if profile_update:
                update_user_profile(user_email, profile_update)
                if user: user.update(profile_update)

            # Save daily log if provided
            if request.daily_log:
                save_daily_log(user_email, request.daily_log.model_dump())

            # Save medical records if provided
            if request.medical_records:
                for record in request.medical_records:
                    save_medical_history(user_email, record.model_dump())

        # Load history
        history = load_user_history(user_email)

        # Build user_data dict for prompt
        user_data = {
            "profile": {
                "age": request.profile.age or (user.get("age") if user else 30),
                "gender": request.profile.gender or (user.get("gender") if user else "other"),
                "existing_conditions": list(set((request.profile.existing_conditions or []) + (user.get("existing_conditions", []) if user else []))),
                "family_history": list(set((request.profile.family_history or []) + (user.get("family_history", []) if user else []))),
            },
            "daily_log": request.daily_log.model_dump() if request.daily_log else {},
            "medical_records": [
                {
                    "illness_description": r.get("illness_description", ""),
                    "prescription_text": r.get("prescription_text", ""),
                    "illness_date": r.get("illness_date", ""),
                }
                for r in history.get("medical_history", [])
            ],
            "vitals": history.get("vitals", []),
            "symptom_analysis_history": history.get("symptom_history", []),
            "historical_trends": {
                "daily_logs": history.get("daily_logs", []),
                "recent_predictions": history.get("recent_predictions", []),
            },
        }

        # Run prediction
        result = run_risk_prediction(user_email, user_data)

        return {
            "status": "success",
            "email": user_email,
            "prediction": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Risk prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocr")
async def extract_prescription_text(file: UploadFile = File(...)):
    """
    Extract text from an uploaded prescription image using OCR.
    Returns the extracted text string.
    """
    try:
        image_bytes = await file.read()
        text = extract_text_from_image(image_bytes)
        return {
            "status": "success",
            "filename": file.filename,
            "extracted_text": text,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")


@router.get("/history/{email}")
async def get_user_history(email: str, days: int = 30):
    """
    Get user's health history (daily logs, medical records, predictions).
    """
    try:
        profile = get_profile(email)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        history = load_user_history(email, days)
        return {
            "status": "success",
            "email": email,
            "profile": profile,
            "history": history,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/daily-log")
async def save_log(user_email: str, log: DailyLogInput):
    """Save a daily health log entry."""
    try:
        ok, err = save_daily_log(user_email, log.model_dump())
        if ok:
            return {"status": "success", "message": "Daily log saved"}
        raise HTTPException(status_code=500, detail=err)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/medical-record")
async def save_record(user_email: str, record: MedicalRecordInput):
    """Save a medical history record."""
    try:
        ok, err = save_medical_history(user_email, record.model_dump())
        if ok:
            return {"status": "success", "message": "Medical record saved"}
        raise HTTPException(status_code=500, detail=err)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
