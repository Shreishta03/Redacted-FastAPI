from app.core import pipeline
from app.schemas.redact import DetectedEntity, RedactResponse

pipeline = pipeline.PIIPipeline()

def redaction_helper(text: str) -> RedactResponse:
    redacted_text, entities = pipeline.run(text)

    api_entities = [
        DetectedEntity(
            entity_type=e.entity_type,
            start=e.start,
            end=e.end,
            score=e.score
        )
        for e in entities
    ]

    return RedactResponse(
        original_text=text,
        redacted_text=redacted_text,
        entities=api_entities
    )
