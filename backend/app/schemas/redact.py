from pydantic import BaseModel
from typing import List

class RedactRequest(BaseModel):
    text: str
    selected_entities: List[str] = None

class DetectedEntity(BaseModel):
    entity_type: str
    start: int
    end: int
    score: float

class RedactResponse(BaseModel):
    original_text: str
    redacted_text: str
    entities: List[DetectedEntity]



