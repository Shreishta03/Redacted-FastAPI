from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
from app.core.config import MAX_PLAIN_TEXT_LENGTH
from app.schemas.redact import RedactRequest, RedactResponse
from app.utils.csv_writer import create_redacted_csv
from app.utils.redaction_helper import redaction_helper
from app.utils.file_size_validator import file_size_validator
from app.services.file_extractors.csv_extractor import extract_redacted_csv_data

from app.services.file_extractors.csv_extractor import (
    get_csv_columns
)

from app.services.file_extractors.pdf_extractor import extract_text_from_pdf
from app.services.file_extractors.docx_extractor import extract_text_from_docx

from app.db.database import get_db
from app.db.crud import create_redaction_log
from app.auth.dependencies import get_current_user

router = APIRouter()

# Plain text redaction
@router.post("/redact", response_model=RedactResponse)
def redact_plain_text(
    request: Request,
    payload: RedactRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    if len(payload.text) > MAX_PLAIN_TEXT_LENGTH:
        raise HTTPException(
            status_code=413,
            detail=f"Input text exceeds maximum allowed length of {MAX_PLAIN_TEXT_LENGTH} characters"
        )
    try:
        pipeline = request.app.state.pii_pipeline
        result = redaction_helper(payload.text, pipeline)

        create_redaction_log(
        db=db,
        user_id=current_user.id,
        input_type="text",
        source_name="plain_text",
        entity_count=len(result.entities)
        )
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Redaction failed: {str(e)}"
        )

# PDF redaction
@router.post("/pdf", response_model=RedactResponse)
async def redact_pdf_file(
    request: Request,
    file: UploadFile = File(...),
    selected_entities: str = Form(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await file.read()
    await file_size_validator(file_bytes)

    try:
        text = extract_text_from_pdf(file_bytes)

        if not text.strip():
            raise HTTPException(status_code=400, detail="No readable text found")

        pipeline = request.app.state.pii_pipeline

        entity_list = None

        if selected_entities is not None:
            try:
                parsed = json.loads(selected_entities)
                if isinstance(parsed, list) and parsed:
                    entity_list = parsed
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid selected_entities format"
                )

        result = redaction_helper(
            text=text,
            pipeline=pipeline,
            selected_entities=entity_list
        )

        create_redaction_log(
            db=db,
            user_id=current_user.id,
            input_type="pdf",
            source_name=file.filename,
            entity_count=len(result.entities)
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF Redaction Failed: {str(e)}"
        )

# DOCX redaction
@router.post("/docx", response_model=RedactResponse)
async def redact_docx_file(
    request: Request,
    file: UploadFile = File(...),
    selected_entities: str = Form(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only DOCX files are supported")

    file_bytes = await file.read()
    await file_size_validator(file_bytes)

    try:
        text = extract_text_from_docx(file_bytes)

        if not text.strip():
            raise HTTPException(status_code=400, detail="No readable text found")

        pipeline = request.app.state.pii_pipeline

        entity_list = None

        if selected_entities is not None:
            try:
                parsed = json.loads(selected_entities)
                if isinstance(parsed, list) and parsed:
                    entity_list = parsed
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid selected_entities format"
                )

        result = redaction_helper(
            text=text,
            pipeline=pipeline,
            selected_entities=entity_list
        )

        create_redaction_log(
            db=db,
            user_id=current_user.id,
            input_type="docx",
            source_name=file.filename,
            entity_count=len(result.entities)
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"DOCX Redaction Failed: {str(e)}"
        )

# CSV column fetch
@router.post("/csv/columns")
async def get_csv_column_names(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
   
    file_bytes = await file.read()

    try:
        columns = get_csv_columns(file_bytes)
        return {"columns": columns}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# CSV redaction
@router.post("/redact/csv")
async def redact_csv_file(
    request: Request,
    file: UploadFile = File(...),
    selected_columns: str = Form(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    file_bytes = await file.read()

    try:
        columns = json.loads(selected_columns)

        headers, redacted_rows = extract_redacted_csv_data(
            file_bytes,
            columns
        )

        csv_file = create_redacted_csv(headers, redacted_rows)

        create_redaction_log(
            db=db,
            user_id=current_user.id,
            input_type="csv",
            source_name=file.filename,
            entity_count=0,
            columns_redacted=columns
        )

        return StreamingResponse(
            csv_file,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=redacted.csv"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect/entities")
async def detect_entities(
    request: Request,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    
    filename = file.filename.lower()

    if not (filename.endswith(".pdf") or filename.endswith(".docx")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported"
        )

    file_bytes = await file.read()
    await file_size_validator(file_bytes)

    try:
        if filename.endswith(".pdf"):
            text = extract_text_from_pdf(file_bytes)
        else:
            text = extract_text_from_docx(file_bytes)

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="No readable text found in document"
            )

        pipeline = request.app.state.pii_pipeline
        _, entities = pipeline.run(text)

        detected_entities = sorted(
            list({e.entity_type for e in entities})
        )

        return {
            "detected_entities": detected_entities
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Entity detection failed: {str(e)}"
        )
