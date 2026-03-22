import os
import json
import logging
from typing import Dict, Any
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)

class AdversarialEngine:
    """Adversarial diagnosis system using GitHub Models"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        if settings.GITHUB_MODELS_TOKEN:
            self.client = OpenAI(
                base_url="https://models.inference.ai.azure.com",
                api_key=settings.GITHUB_MODELS_TOKEN,
            )
        else:
            logger.warning("GITHUB_MODELS_TOKEN not set in AdversarialEngine")

    def _format_symptoms(self, symptoms: Any) -> str:
        """Normalize symptoms to string for prompt inclusion"""
        if isinstance(symptoms, list):
            return "\n".join([
                f"- {getattr(s, 'description', str(s))} (Severity: {getattr(s, 'severity', 'N/A')})"
                for s in symptoms
            ])
        return str(symptoms) if symptoms else "No symptoms provided"

    def prosecutor_ai(self, patient_data: dict) -> Dict[str, Any]:
        """Argues FOR the most likely diagnosis"""
        if not self.client:
            return {"error": "AI client not initialized"}
            
        symptoms_desc = self._format_symptoms(patient_data.get('symptoms'))
        
        location_ctx = f"Location: {patient_data.get('location_city', 'Unknown')}, {patient_data.get('location_country', 'Unknown')}"
        
        prompt = f"""You are the PROSECUTOR AI in a medical debate.
Your job: Argue STRONGLY for the MOST LIKELY standard diagnosis based on symptoms and epidemiology.

Patient: {patient_data.get('age')}yo {patient_data.get('gender')}
{location_ctx}
Symptoms: {symptoms_desc}
Medical history: {patient_data.get('history', 'None significant.')}

CRITICAL: Focus on common local diseases (epidemiology) and distinguishing signs (e.g., bleeding in Dengue).

Respond strictly in JSON:
{{
    "diagnosis": "Name of Diagnosis",
    "confidence": 0-100,
    "points": [
        {{ "title": "Evidence A", "description": "Why this supports your diagnosis." }},
        {{ "title": "Evidence B", "description": "Why this supports your diagnosis." }}
    ]
}}
"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an aggressive prosecutor AI. Focus on the most probable diagnosis."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Prosecutor AI Error: {e}")
            return {"diagnosis": "Unavailable", "confidence": 0, "points": []}

    def defense_ai(self, patient_data: dict, prosecutor_diagnosis: str) -> Dict[str, Any]:
        """Searches for contradictions and alternatives"""
        if not self.client:
            return {"error": "AI client not initialized"}

        symptoms_desc = self._format_symptoms(patient_data.get('symptoms'))
        
        location_ctx = f"Location: {patient_data.get('location_city', 'Unknown')}, {patient_data.get('location_country', 'Unknown')}"
        
        prompt = f"""You are the DEFENSE AI in a medical debate.
The Prosecutor claims: "{prosecutor_diagnosis}"

Your job: Find a RARE or ALTERNATIVE diagnosis that fits the facts but contradicts the Prosecutor.
CRITICAL: Even if the Prosecutor is likely correct, you MUST find a scientific alternative for a robust conflict resolution.

Patient: {patient_data.get('age')}yo {patient_data.get('gender')}
{location_ctx}
Symptoms: {symptoms_desc}

Respond strictly in JSON:
{{
    "diagnosis": "Alternative Diagnosis Name",
    "confidence": 0-100,
    "points": [
        {{ "title": "Counter-Point A", "description": "Evidence typical for this rare condition." }},
        {{ "title": "Counter-Point B", "description": "Why the prosecutor's evidence is flawed." }}
    ]
}}
"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a defense AI. Find contradictions and rare alternatives."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Defense AI Error: {e}")
            return {"diagnosis": "Unavailable", "confidence": 0, "points": []}

    def judge_ai(self, patient_data: dict, prosecutor_result: dict, defense_result: dict) -> Dict[str, Any]:
        """Synthesizes both arguments for a patient verdict"""
        if not self.client:
            return {"error": "AI client not initialized"}

        location_ctx = f"Location: {patient_data.get('location_city', 'Unknown')}, {patient_data.get('location_country', 'Unknown')}"
        
        prompt = f"""You are the JUDGE AI in a medical debate.
        
Your Goal: Evaluate the debate and provide a final verdict for the PATIENT.

Patient Profile:
{location_ctx}
Symptoms: {self._format_symptoms(patient_data.get('symptoms'))}

CONTEXT:
PROSECUTOR argues: {prosecutor_result['diagnosis']} (Usually the most probable/common diagnosis)
DEFENSE argues: {defense_result['diagnosis']} (Usually a rare or alternative diagnosis for stress-testing)

CRITERIA:
1. Clinical Probability: Is the diagnosis common or extremely rare for these symptoms?
2. Evidence Strength: Which agent provided more specific points related to the patient's symptoms?
3. Urgency: If both are possible, prioritize the one that requires more immediate medical attention.

Respond strictly in JSON:
{{
    "verdict": "Final Diagnosis Name",
    "confidence": 0-100,
    "highlights": [
        "First key takeaway for the patient",
        "Second key takeaway",
        "Third key takeaway"
    ],
    "synthesis": "A balanced explanation of why you reached this verdict, acknowledging the alternative but explaining why the chosen one is more likely or urgent. Use simple language.",
    "next_step": "One clear action the patient should take next."
}}
"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an impartial judge. Your final verdict MUST be simple for a patient to understand."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Judge AI Error: {e}")
            return {
                "verdict": "Unavailable",
                "confidence": 0,
                "highlights": ["Check back soon", "Error in analysis"],
                "synthesis": "We encountered an error processing the medical debate.",
                "next_step": "Seek professional medical advice."
            }

    def run_debate(self, patient_data: dict) -> Dict[str, Any]:
        """Run full adversarial debate"""
        # Step 1: Prosecutor argues
        prosecutor = self.prosecutor_ai(patient_data)
        
        # Step 2: Defense counters
        defense = self.defense_ai(patient_data, prosecutor.get("diagnosis", "Unknown"))
        
        # Step 3: Judge synthesizes
        verdict = self.judge_ai(patient_data, prosecutor, defense)
        
        return {
            "prosecutor": prosecutor,
            "defense": defense,
            "verdict": verdict
        }

adversarial_engine = AdversarialEngine()
