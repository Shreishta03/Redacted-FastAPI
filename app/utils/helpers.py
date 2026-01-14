from app.schemas.redact import DetectedEntity, RedactResponse

def redaction_helper(text: str, pipeline) -> RedactResponse:
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
