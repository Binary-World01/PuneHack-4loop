"""
Diagnosis Router - Standard symptom analysis
"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime
from app.schemas import PatientProfile, DiagnosisResult
from app.services.llm_service import llm_service
from app.services.outbreak_db import save_to_database
from app.services.location_service import get_client_location

router = APIRouter(prefix="/diagnosis", tags=["Diagnosis"])


@router.post("/analyze", response_model=DiagnosisResult)
async def analyze_symptoms(patient: PatientProfile, request: Request):
    """Analyze patient symptoms and provide diagnosis"""
    try:
        result = llm_service.analyze_symptoms(patient)
        
        # Detect location for database record, prioritizing patient-provided location
        location_data = await get_client_location(
            request, 
            patient.latitude, 
            patient.longitude, 
            patient.location_city, 
            patient.location_country
        )
        
        # Prepare data for save_to_database
        save_data = {
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "symptoms": str(patient.symptoms),
            "severity": patient.severity,
            "duration": patient.duration,
            "user_email": getattr(patient, 'email', None) or "anonymous@neurovitals.ai"
        }
        
        # Save to database so it appears in Admin/Map
        save_to_database(
            save_data, 
            ai_response=f"Diagnosis: {result['primary_diagnosis']}\nReasoning: {', '.join(result['reasoning'])}",
            location_data=location_data
        )
        
        return DiagnosisResult(
            primary_diagnosis=result["primary_diagnosis"],
            confidence=result["confidence"],
            reasoning=result["reasoning"],
            recommendations=result["recommendations"],
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "diagnosis"}
