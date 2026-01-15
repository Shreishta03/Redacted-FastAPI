from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
import json
from app.core.config import MAX_PLAIN_TEXT_LENGTH
from app.schemas.redact import RedactRequest, RedactResponse
from app.utils.file_size_validator import file_size_validator
from app.utils.redaction_helper import redaction_helper

from app.services.file_extractors.csv_extractor import (
    get_csv_columns,
    extract_selected_columns_as_text
)

from app.services.file_extractors.pdf_extractor import extract_text_from_pdf
from app.services.file_extractors.docx_extractor import extract_text_from_docx

from app.db.database import get_db
from app.db.models import RedactionLog
from app.db.crud import create_redaction_log

router = APIRouter()

# Plain text redaction
@router.post("/redact", response_model=RedactResponse)
def redact_plain_text(
    request: Request,
    payload: RedactRequest,
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
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    file_bytes = await file.read()
    await file_size_validator(file_bytes)

    try:
        text = extract_text_from_pdf(file_bytes)
        pipeline = request.app.state.pii_pipeline
        result = redaction_helper(text, pipeline)

        create_redaction_log(
        db=db,
        input_type="pdf",
        source_name=file.filename,
        entity_count=len(result.entities)
    )
        return result

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
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only DOCX files are supported")
    file_bytes = await file.read()
    await file_size_validator(file_bytes)

    try:
        text = extract_text_from_docx(file_bytes)
        pipeline = request.app.state.pii_pipeline
        result = redaction_helper(text, pipeline)

        create_redaction_log(
        db=db,
        input_type="docx",
        source_name=file.filename,
        entity_count=len(result.entities)
    )
        return result

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
@router.post("/redact/csv", response_model=RedactResponse)
async def redact_csv_file(
    request: Request,
    file: UploadFile = File(...),
    selected_columns: str = Form(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    file_bytes = await file.read()
    await file_size_validator(file_bytes)

    try:
        try:
            columns = json.loads(selected_columns)
        except json.JSONDecodeError:
            columns = [c.strip() for c in selected_columns.split(",") if c.strip()]

        text = extract_selected_columns_as_text(file_bytes, columns)
        pipeline = request.app.state.pii_pipeline
        result = redaction_helper(text, pipeline)

        create_redaction_log(
        db=db,
        input_type="csv",
        source_name=file.filename,
        entity_count=len(result.entities),
        columns_redacted=columns
    )
        return result

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        raise HTTPException(status_code=500, detail="CSV redaction failed")
