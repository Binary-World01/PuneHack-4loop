"""
Outbreak Database Service – Supabase CRUD for patient records,
admin outbreak tracking, and map queries.

Migrated from hackathon_project1/supabase_service.py.
Uses the same Supabase instance as the rest of the app.
"""

import uuid
import math
import logging
from datetime import datetime, timedelta

from supabase import create_client, Client
from app.config import settings
from app.services.disease_classifier import DiseaseClassifier

logger = logging.getLogger(__name__)

# Initialise Supabase client
_supabase: Client | None = None


def _get_sb() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase


# ──────────────────────────────────────────────
#  Housekeeping
# ──────────────────────────────────────────────
def cleanup_old_records():
    """Delete admin records older than 20 days."""
    try:
        cutoff = (datetime.now() - timedelta(days=20)).isoformat()
        result = _get_sb().table("admin").delete().lt("created_at", cutoff).execute()
        if result.data:
            logger.info("Cleaned up %d old outbreak records", len(result.data))
    except Exception as exc:
        logger.error("Cleanup error: %s", exc)


# ──────────────────────────────────────────────
#  File upload
# ──────────────────────────────────────────────
def upload_file(file, bucket_name: str = "medical_files") -> str | None:
    try:
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "bin"
        unique_name = f"{uuid.uuid4()}.{ext}"
        file_content = file.file.read()

        _get_sb().storage.from_(bucket_name).upload(
            path=unique_name,
            file=file_content,
            file_options={"content-type": file.content_type},
        )
        return str(_get_sb().storage.from_(bucket_name).get_public_url(unique_name))
    except Exception as exc:
        logger.error("Upload error: %s", exc)
        return None


# ──────────────────────────────────────────────
#  Save patient + admin record
# ──────────────────────────────────────────────
def save_to_database(
    data: dict,
    ai_response: str | None = None,
    image_url: str | None = None,
    location_data: dict | None = None,
) -> int | None:
    try:
        # 1. Get form_id from medical_forms (linkage)
        email = data.get("email") or data.get("user_email")
        form_id = None
        if email:
            f_res = _get_sb().table("medical_forms").select("formid").eq("user_email", email).order("updated_at", desc=True).limit(1).execute()
            if f_res.data:
                form_id = f_res.data[0]["formid"]

        patient_record = {
            "form_id": form_id,
            "symptoms_data": {
                "name": data.get("name"),
                "age": data.get("age"),
                "gender": data.get("gender"),
                "symptoms": data.get("symptoms"),
                "severity": data.get("severity"),
                "duration": data.get("duration"),
                "ai_response": ai_response,
                "image_url": image_url,
            },
            "risk_level": data.get("severity") or "Low",
            "recorded_at": datetime.now().isoformat(),
        }

        result = _get_sb().table("records").insert(patient_record).execute()

        if result.data:
            p_id = result.data[0]["p_id"]

            # Classify disease for admin/map
            classification = DiseaseClassifier.classify_disease(ai_response)

            if location_data and location_data.get("latitude"):
                # Defensive check for admin table
                try:
                    admin_record = {
                        "latitude": location_data.get("latitude"),
                        "longitude": location_data.get("longitude"),
                        "location_city": location_data.get("city"),
                        "location_region": location_data.get("region"),
                        "location_country": location_data.get("country"),
                        "location": location_data.get("exact_location"),
                        "symptoms": f"{classification.get('disease_type')} | PRECAUTION: {classification.get('precautions')}",
                        "disease_category": classification.get("category"),
                        "spreadable": classification.get("spreadable"),
                        "created_at": datetime.now().isoformat(),
                    }
                    _get_sb().table("admin").insert(admin_record).execute()
                except Exception as admin_exc:
                    logger.warning("Admin (geolocation) table error: %s", admin_exc)

            logger.info("Saved patient record %s", p_id)
            return p_id

    except Exception as exc:
        logger.error("Database save error: %s", exc)
    return None


# ──────────────────────────────────────────────
#  Helpers & Classification
# ──────────────────────────────────────────────
def is_viral(disease_name: str) -> bool:
    """Check if a disease name suggests a viral infection."""
    if not disease_name:
        return False
    viral_keywords = [
        "viral", "flu", "influenza", "covid", "dengue", "chikungunya", 
        "measles", "mumps", "rubella", "hepatitis", "herpes", "hiv",
        "ebola", "zika", "rabies", "cold", "rhinovirus"
    ]
    name_lower = disease_name.lower()
    return any(kw in name_lower for kw in viral_keywords)


# ──────────────────────────────────────────────
#  Map queries
# ──────────────────────────────────────────────
def get_spreadable_diseases_for_map(only_viral: bool = True) -> list:
    """Return outbreak records for the map. Filters for viral if only_viral=True."""
    try:
        cutoff = (datetime.now() - timedelta(days=20)).isoformat()
        
        # Base query
        query = _get_sb().table("admin").select(
            "id, latitude, longitude, location_city, location_region, "
            "disease_type, disease_category, created_at, spreadable, "
            "records:patient_id (p_id, symptoms_data, risk_level)"
        ).gte("created_at", cutoff).not_.is_("latitude", "null")

        result = query.execute()
        data = result.data or []

        if only_viral:
            # Filter in Python for complexity vs simple SQL ilike
            data = [
                r for r in data 
                if is_viral(r.get("disease_type")) or r.get("disease_category") == "flu_like"
            ]
            
        return data
    except Exception as exc:
        logger.warning("Admin table query failed: %s", exc)
        return []


def get_all_patients_for_admin() -> list:
    """Return every patient record with location info directly from the admin table."""
    try:
        # Fetch directly from admin table as join is failing in this environment
        result = (
            _get_sb()
            .table("admin")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return result.data
    except Exception as exc:
        logger.error("Admin query error: %s", exc)
        # Fallback to records if admin join fails
        try:
            res = _get_sb().table("records").select("*").order("recorded_at", desc=True).execute()
            return [{"records": r} for r in res.data]
        except:
            return []


def get_nearby_outbreaks(user_lat: float, user_lng: float, radius_km: float = 10) -> list:
    """Return spreadable outbreaks within a bounding box around the user."""
    try:
        lat_diff = radius_km / 111.0
        lng_diff = radius_km / (111.0 * abs(math.cos(math.radians(user_lat))))

        result = (
            _get_sb()
            .table("admin")
            .select("*, records:patient_id (name, symptoms, severity)")
            .eq("spreadable", True)
            .gte("latitude", user_lat - lat_diff)
            .lte("latitude", user_lat + lat_diff)
            .gte("longitude", user_lng - lng_diff)
            .lte("longitude", user_lng + lng_diff)
            .execute()
        )
        return result.data
    except Exception as exc:
        logger.error("Nearby query error: %s", exc)
        return []
