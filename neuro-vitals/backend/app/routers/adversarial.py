"""
Adversarial Router - Adversarial diagnosis debate
"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime
from app.schemas import PatientProfile, AdversarialDebateResult
from app.services.adversarial_engine import adversarial_engine

from app.services.location_service import get_client_location
from app.services.outbreak_db import save_to_database

router = APIRouter(prefix="/adversarial", tags=["Adversarial"])


@router.post("/debate", response_model=AdversarialDebateResult)
async def run_adversarial_debate(patient: PatientProfile, request: Request):
    """Run adversarial diagnosis debate"""
    try:
        # Detect location if not provided
        location_data = await get_client_location(
            request,
            patient.latitude,
            patient.longitude,
            patient.location_city,
            patient.location_country
        )

        patient_profile_dict = patient.dict()

        # Ensure location is synced back to profile dict if needed by engine
        patient_profile_dict.update({
            "latitude": location_data.get("latitude"),
            "longitude": location_data.get("longitude"),
            "location_city": location_data.get("city"),
            "location_country": location_data.get("country")
        })

        # 2. Run debate
        result = adversarial_engine.run_debate(patient_profile_dict)

        # 3. Persist for admin mapping
        save_data = {
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "symptoms": str(patient.symptoms),
            "severity": patient.severity,
            "duration": patient.duration,
            "user_email": getattr(patient, 'email', None) or "anonymous@neurovitals.ai"
        }
        
        verdict_text = result["verdict"].get("verdict", "Unknown")
        synthesis = result["verdict"].get("synthesis", "")
        
        save_to_database(
            save_data,
            ai_response=f"ADVERSARIAL VERDICT: {verdict_text}\nSynthesis: {synthesis}",
            location_data=location_data
        )
        
        return AdversarialDebateResult(
            prosecutor=result["prosecutor"],
            defense=result["defense"],
            verdict=result["verdict"],
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debate failed: {str(e)}")
