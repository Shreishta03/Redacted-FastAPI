from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from app.schemas.redact import RedactRequest, RedactResponse

from fastapi import UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
import json

from app.services.file_extractors.csv_extractor import get_csv_columns
from fastapi import UploadFile, File, HTTPException, Form
from app.services.file_extractors.csv_extractor import extract_selected_columns_as_text
from app.services.file_extractors.pdf_extractor import extract_text_from_pdf
from app.services.file_extractors.docx_extractor import extract_text_from_docx
from app.utils.helpers import redaction_helper

from app.db.models import RedactionLog
from app.db.crud import get_db

router = APIRouter()

# Plain text redaction
@router.post("/redact", response_model=RedactResponse)
def redact_plain_text(
    request: RedactRequest,
    db: Session = Depends(get_db) 
):
    try:
        result = redaction_helper(request.text)

        log = RedactionLog(
                input_type="text",
                source_name="plain_text",
                entity_count=len(result.entities),
                columns_redacted=None
        )
        db.add(log)
        db.commit()

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Reduction failed: {str(e)}"
        )


# PDF redaction
@router.post("/pdf", response_model=RedactResponse)
async def redact_pdf_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)  
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await file.read()

    try:
        text = extract_text_from_pdf(file_bytes)
        result = redaction_helper(text)

        log = RedactionLog(
            input_type="pdf",
            source_name=file.filename,
            entity_count=len(result.entities),
            columns_redacted=None
        )
        db.add(log)
        db.commit()

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF Redaction Failed: {str(e)}"
        )


# DOCX redaction
@router.post("/docx", response_model=RedactResponse)
async def redact_docx_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)  
):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only DOCX files are supported")

    file_bytes = await file.read()
    try:
        text = extract_text_from_docx(file_bytes)
        result = redaction_helper(text)

        log = RedactionLog(
            input_type="docx",
            source_name=file.filename,
            entity_count=len(result.entities),
            columns_redacted=None
        )
        db.add(log)
        db.commit()

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

    try:
        try:
            columns = json.loads(selected_columns)
        except json.JSONDecodeError:
            columns = [col.strip() for col in selected_columns.split(",") if col.strip()]

        text = extract_selected_columns_as_text(file_bytes, columns)
        result = redaction_helper(text)

        #DB SAVE (ADDED)
        log = RedactionLog(
            input_type="csv",
            source_name=file.filename,
            entity_count=len(result.entities),
            columns_redacted=json.dumps(columns)
        )
        db.add(log)
        db.commit()

        return result

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        raise HTTPException(status_code=500, detail="CSV redaction failed")
