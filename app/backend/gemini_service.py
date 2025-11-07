import os
import logging
from google import genai
from pydantic import BaseModel, Field
from typing import Optional
import json

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")


class MedicineAlternative(BaseModel):
    name: str
    price_range: str


class MedicineInfo(BaseModel):
    medicine_name: str
    generic_alternatives: list[MedicineAlternative]
    notes: str


PROMPT_TEMPLATE = """You are an AI medical assistant. Your task is to provide generic alternatives for a given medicine, along with an approximate price comparison in USD. Be concise and clear.

Medicine: {medicine_name}

Provide the response in a structured JSON format. The JSON object must conform to this Pydantic model:

pydantic
from pydantic import BaseModel, Field
from typing import List

class MedicineAlternative(BaseModel):
    name: str
    price_range: str

class MedicineInfo(BaseModel):
    medicine_name: str
    generic_alternatives: List[MedicineAlternative]
    notes: str


Do not include any introductory text or code block formatting in your final JSON output. Just return the raw JSON object.
"""


def get_medicine_alternatives(medicine_name: str) -> Optional[MedicineInfo]:
    if not GOOGLE_API_KEY:
        logging.error("GOOGLE_API_KEY is not set. Cannot contact Gemini API.")
        return None
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
        prompt = PROMPT_TEMPLATE.format(medicine_name=medicine_name)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json", response_schema=MedicineInfo
            ),
        )
        if response.parts:
            return MedicineInfo.model_validate_json(response.text)
        else:
            logging.warning("Gemini API returned an empty response.")
            return None
    except Exception as e:
        logging.exception(f"Error fetching medicine alternatives from Gemini: {e}")
        return None