from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from supabase import create_client, Client
from app.config import settings

# Initialize router
router = APIRouter(prefix="/vitals", tags=["Vitals"])

# Define data models
class VitalsData(BaseModel):
    user_email: str
    user_id: Optional[str] = None
    steps: Optional[int] = 0
    heart_rate: Optional[int] = 0
    sleep_hours: Optional[float] = 0.0
    calories: Optional[int] = 0
    source: Optional[str] = "google_fit_mock"
    recorded_at: Optional[datetime] = None

# Helper to get supabase client
def _get_supabase() -> Optional[Client]:
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    if not url or not key:
        return None
    return create_client(url, key)

@router.post("/save-vitals")
async def save_vitals(vitals: VitalsData):
    """Save vitals data to Supabase (upsert)"""
    supabase = _get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        print(f"[Supabase] Received vitals data for user_email: {vitals.user_email}")
        
        # Prepare data for Supabase
        data = {
            "user_email": vitals.user_email,
            "steps": vitals.steps or 0,
            "heart_rate": vitals.heart_rate or 0,
            "sleep_hours": float(vitals.sleep_hours or 0),
            "calories": vitals.calories or 0,
            "source": vitals.source,
            "recorded_at": (vitals.recorded_at or datetime.now()).isoformat()
        }
        
        update_result = supabase.table("user_vitals")\
            .update(data)\
                .eq("user_email", vitals.user_email)\
            .execute()
        
        if not update_result.data:
            print(f"[Supabase] No existing record for user_email, inserting new one...")
            result = supabase.table("user_vitals").insert(data).execute()
        else:
            print(f"[Supabase] Updated existing record for user_email {vitals.user_email}")
            result = update_result
        
        return {
            "status": "success", 
            "message": "Vitals saved to Supabase",
            "data": result.data
        }
    
    except Exception as e:
        print(f"[Supabase] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-vitals/{user_email}")
async def get_vitals(user_email: str):
    """Get vitals for a specific user email"""
    supabase = _get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        result = supabase.table("user_vitals").select("*").eq("user_email", user_email).order("recorded_at", desc=True).limit(1).execute()
        return {"status": "success", "data": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))