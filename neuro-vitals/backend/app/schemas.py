"""
Pydantic schemas for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union
from datetime import datetime
from enum import Enum


class SymptomInput(BaseModel):
    """Individual symptom entry"""
    description: str = Field(..., description="Symptom description")
    severity: int = Field(..., ge=1, le=10, description="Severity 1-10")
    duration_days: int = Field(..., ge=0, description="How long has this lasted")
    onset_time: Optional[str] = Field(None, description="morning/afternoon/evening/night")


class PatientProfile(BaseModel):
    """Complete patient profile"""
    patient_id: Optional[str] = "P-123" # Default or optional
    name: Optional[str] = "Patient"
    age: int
    gender: str
    symptoms: Union[List[SymptomInput], str] # Support both structured and plain text
    medical_history: Optional[List[str]] = Field(default_factory=list)
    current_medications: Optional[List[str]] = Field(default_factory=list)
    severity: Optional[int] = 5
    duration: Optional[int] = 1
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_city: Optional[str] = None
    location_country: Optional[str] = None


class DiagnosisResult(BaseModel):
    """Standard diagnosis result"""
    primary_diagnosis: str
    confidence: float = Field(..., ge=0, le=1)
    reasoning: List[str]
    recommendations: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AdversarialDebateResult(BaseModel):
    """Result from adversarial diagnosis engine"""
    prosecutor: dict
    defense: dict
    verdict: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TrajectoryForecast(BaseModel):
    """Health trajectory forecast"""
    current_risk: float
    baseline_projection: dict
    intervention_projection: dict
    diagnosis: str
    key_interventions: List[str]


class CommunityHealthData(BaseModel):
    """Community health intelligence"""
    total_reports: int
    recent_24h: int
    transmission_velocity: float
    trending_symptoms: List[tuple]
    area_data: List[dict]
    map_points: List[dict]
