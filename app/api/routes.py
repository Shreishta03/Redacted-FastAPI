from fastapi import APIRouter, HTTPException
from app.schemas.redact import RedactRequest, DetectedEntity, RedactResponse
from app.core.pipeline import PIIPipeline

router = APIRouter()

pipeline = PIIPipeline()

@router.post("/redact", response_model=RedactResponse)
def redact_text(request: RedactRequest):
    try:
        redacted_text, entities = pipeline.run(request.text)

        api_entities = []

        for e in entities:
            api_entity = DetectedEntity(
                entity_type=e.entity_type,
                start=e.start,
                end=e.end,
                score=e.score
            )
            api_entities.append(api_entity)

        return RedactResponse(
            original_text=request.text,
            redacted_text=redacted_text,
            entities=api_entities
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Reduction failed: {str(e)}"
        )
