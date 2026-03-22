import logging
import base64
from app.config import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

# Lazy-load the client (only on first call)
_client = None


def _get_client():
    global _client
    if _client is None:
        if not settings.GITHUB_MODELS_TOKEN:
            logger.warning("GITHUB_MODELS_TOKEN not set, using mock/failing")
            return None
            
        _client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=settings.GITHUB_MODELS_TOKEN,
        )
    return _client


def analyze_symptoms_with_gemini(data: dict, image_file=None) -> dict:
    """
    Analyse patient symptoms (and optional image) with GitHub Models (GPT-4o).
    
    Parameters
    ----------
    data : dict  – must contain name, age, gender, symptoms, severity, duration
    image_file   – optional FastAPI UploadFile
    """
    try:
        client = _get_client()
        if not client:
            return {"analysis": "AI service error: No API key configured."}

        prompt = f"""
        You are an AI Medical Assistant specializing in neurological and general health.
        Analyze the following patient data.

        Patient Name: {data['name']}
        Age: {data['age']}, Gender: {data['gender']}
        Symptoms: {data['symptoms']}
        Severity: {data['severity']}/10, Duration: {data['duration']} days

        Instructions:
        1. Identify the POSSIBLE CONDITION.
        2. Provide a section called IMPORTANT POINTS (3-5 short, punchy bullet points for quick reading).
        3. Provide a section called WHY THIS HAPPENS (Easy Explanation) (avoid any medical jargon, use analogies, explain strictly for a patient).
        4. Provide clear PREVENTIVE MEASURES.
        5. Provide clear NEXT STEPS.
        
        DISCLAIMER: State this is AI analysis.

        CRITICAL: Use simple, friendly language throughout. Arrange the content logically.

        CRITICAL: Your output MUST contain exactly the following markers (sections) to be parsed correctly by the system. If you omit them, the system will fail. 
        
        USE THESE EXACT MARKERS (DO NOT CHANGE THEM):
        ## CONDITION
        ## IMPORTANT POINTS
        ## WHY THIS HAPPENS
        ## PREVENTIVE MEASURES
        ## NEXT STEPS
        ## DISCLAIMER

        Example of a Correct Response:
        ## CONDITION
        Flu-like Syndrome
        
        ## IMPORTANT POINTS
        - Point 1
        - Point 2
        
        (followed by other sections)

        CRITICAL: Do NOT omit the ## symbols. They are MANDATORY for programmatic parsing. Do not include any text before the first section.
        """

        messages = [
            {
                "role": "system",
                "content": "You are a professional medical assistant. Your response MUST follow the ## [SECTION] format strictly."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ]
            }
        ]

        # Handle optional image
        if image_file and getattr(image_file, "filename", None):
            image_file.file.seek(0)
            image_data = image_file.file.read()
            base64_image = base64.b64encode(image_data).decode("utf-8")
            
            mime_type = getattr(image_file, "content_type", "image/jpeg")
            
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_image}"
                }
            })
            logger.info("Image attached to GitHub Models requested")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.1,
            max_tokens=2048
        )
        
        return {"analysis": response.choices[0].message.content}

    except Exception as exc:
        logger.error("GitHub Models error: %s", exc)
        return {"analysis": f"AI service error. Please try again. Error: {exc}"}
