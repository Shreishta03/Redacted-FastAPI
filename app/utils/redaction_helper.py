from typing import List, Optional
from app.schemas.redact import DetectedEntity, RedactResponse

def redaction_helper(
    text: str,
    pipeline,
    selected_entities: Optional[List[str]] = None
) -> RedactResponse:

    redacted_text, entities = pipeline.run(text)

    # If no filtering → return default behavior
    if not selected_entities:
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

    # Filter entities by selected types
    filtered_entities = [
        e for e in entities
        if e.entity_type in selected_entities
    ]

    # Manual redaction
    redacted_chars = list(text)

    text_length = len(text)

    for e in filtered_entities:
            start = max(0, e.start)
            end = min(text_length, e.end)

            for i in range(start, end):
                redacted_chars[i] = "*"


    filtered_redacted_text = "".join(redacted_chars)

    api_entities = [
        DetectedEntity(
            entity_type=e.entity_type,
            start=e.start,
            end=e.end,
            score=e.score
        )
        for e in filtered_entities
    ]

    return RedactResponse(
        original_text=text,
        redacted_text=filtered_redacted_text,
        entities=api_entities
    )
