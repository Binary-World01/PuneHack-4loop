"""
Disease Classifier – categorises AI diagnosis output as
spreadable (flu-like / other) or non-spreadable so that only
contagious cases appear on the community outbreak map.

Migrated from hackathon_project1.
"""


class DiseaseClassifier:
    # Spreadable diseases (flu-like) – RED on map
    FLU_LIKE_DISEASES = [
        "influenza", "flu", "covid", "covid-19", "sars-cov-2",
        "common cold", "cold", "respiratory infection", "bronchitis",
        "pneumonia", "whooping cough", "rsv", "throat infection",
        "breathing issues", "body aches", "fever", "cough", "sore throat",
        "runny nose", "congestion", "sinus infection", "flu-like",
    ]

    # Other spreadable (Tropical/Vector-borne) – ORANGE on map
    OTHER_SPREADABLE = [
        "dengue", "malaria", "typhoid", "cholera", "zika", "chikungunya",
        "strep throat", "staphylococcus", "e. coli", "salmonella",
        "hepatitis", "tuberculosis", "measles", "chickenpox",
        "meningitis", "conjunctivitis", "pink eye", "norovirus",
        "skin infection", "rash", "fungal infection", "bacterial infection",
        "stomach flu", "gastroenteritis", "food poisoning",
    ]

    # Non-spreadable conditions – GREEN on map
    NON_SPREADABLE = [
        "anxiety", "migraine", "headache", "asthma", "allergy", "allergies",
        "diabetes", "hypertension", "arthritis", "back pain",
        "depression", "insomnia", "constipation",
        "indigestion", "acidity", "dehydration", "fatigue",
        "acne", "skin roughness", "dryness", "swelling", "eczema",
        "psoriasis", "dermatitis", "hair loss", "dandruff",
    ]

    # Specific Precautions Map
    PRECAUTIONS_MAP = {
        # Flu-like
        "dengue": "Avoid stagnant water, use mosquito nets, and monitor platelet counts.",
        "malaria": "Use mosquito repellents, sleep under nets, and start antimalarials if prescribed.",
        "covid": "Isolate, wear N95 mask, and monitor blood oxygen levels.",
        "influenza": "Rest, hydrate, and avoid contact with elderly or infants.",
        "flu": "Rest, hydrate, and avoid contact with elderly or infants.",
        "pneumonia": "Deep breathing exercises, stay warm, and follow antibiotic course strictly.",
        "typhoid": "Drink boiled water, avoid raw food, and maintain strict hand hygiene.",
        "cholera": "ORS rehydration, boiled water, and immediate clinical consultation.",
        # Common symptoms
        "fever": "Monitor temperature hourly and stay hydrated.",
        "cough": "Warm fluids and avoid cold drinks.",
        # Default category precautions
        "flu_like": "Practice social distancing, wear masks, and sanitize frequently.",
        "other_spreadable": "Wash hands with soap, avoid sharing personal items, and follow local health advisories.",
        "non_spreadable": "Monitor symptoms and consult a professional if they persist.",
    }

    @classmethod
    def classify_disease(cls, ai_response: str | None) -> dict:
        """Return category, spreadable flag, marker colour, specific disease type, and precautions."""
        if not ai_response:
            return {
                "category": "unknown",
                "spreadable": False,
                "marker_color": "gray",
                "disease_type": "unknown",
                "precautions": "No data for assessment."
            }

        lower = ai_response.lower()

        for disease in cls.FLU_LIKE_DISEASES:
            if disease in lower:
                return {
                    "category": "flu_like",
                    "spreadable": True,
                    "marker_color": "red",
                    "disease_type": disease,
                    "precautions": cls.PRECAUTIONS_MAP.get(disease, cls.PRECAUTIONS_MAP["flu_like"])
                }

        for disease in cls.OTHER_SPREADABLE:
            if disease in lower:
                return {
                    "category": "other_spreadable",
                    "spreadable": True,
                    "marker_color": "orange",
                    "disease_type": disease,
                    "precautions": cls.PRECAUTIONS_MAP.get(disease, cls.PRECAUTIONS_MAP["other_spreadable"])
                }

        for condition in cls.NON_SPREADABLE:
            if condition in lower:
                return {
                    "category": "non_spreadable",
                    "spreadable": False,
                    "marker_color": "green",
                    "disease_type": condition,
                    "precautions": cls.PRECAUTIONS_MAP.get(condition, cls.PRECAUTIONS_MAP["non_spreadable"])
                }

        return {
            "category": "unknown",
            "spreadable": False,
            "marker_color": "gray",
            "disease_type": "generic condition",
            "precautions": cls.PRECAUTIONS_MAP["non_spreadable"]
        }
