from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
import io

from app.core.config import MAX_PLAIN_TEXT_LENGTH
from app.schemas.redact import RedactRequest, RedactResponse
from app.utils.csv_writer import create_redacted_csv

from app.utils.docx_redactor import (
    redact_docx_paragraphwise,
    redact_docx_preview
)

from app.utils.redaction_helper import redaction_helper
from app.utils.file_size_validator import file_size_validator
from app.services.file_extractors.csv_extractor import (
    extract_redacted_csv_data,
    get_csv_columns,
    get_redacted_csv_preview
)

from app.services.file_extractors.docx_extractor import extract_text_from_docx

from app.db.database import get_db
from app.schemas.user import UserStats
from app.db.crud import create_redaction_log, get_user_stats, check_user_upload_limit
from app.auth.dependencies import get_current_user

router = APIRouter()

# Plain text redaction
@router.post("/redact")
def redact_plain_text(
    request: Request,
    payload: RedactRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not check_user_upload_limit(db, current_user.id):
        raise HTTPException(
            status_code=429,
            detail="Daily upload limit reached"
        )
    
    if len(payload.text) > MAX_PLAIN_TEXT_LENGTH:
        raise HTTPException(
            status_code=413,
            detail=f"Input text exceeds maximum allowed length of {MAX_PLAIN_TEXT_LENGTH} characters"
        )
    try:
        pipeline = request.app.state.pii_pipeline
        result = redaction_helper(payload.text, pipeline, payload.selected_entities)

        create_redaction_log(
        db=db,
        user_id=current_user.id,
        input_type="text",
        source_name="plain_text",
        entity_count=len(result.entities)
        )
        return StreamingResponse(
            io.StringIO(result.redacted_text),
            media_type="text/plain"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Redaction failed: {str(e)}"
        )

# PDF redaction
from app.utils.pdf_redactor import (
    redact_pdf_file as redact_pdf_file_util,
    redact_pdf_preview
)

@router.post("/pdf")
async def redact_pdf_file(
    request: Request,
    file: UploadFile = File(...),
    selected_entities: str = Form(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not check_user_upload_limit(db, current_user.id):
        raise HTTPException(status_code=429, detail="Daily upload limit reached")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await file.read()
    await file_size_validator(file_bytes)

    try:
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

        pdf_file, entity_count = redact_pdf_file_util(
            file_bytes=file_bytes,
            pipeline=pipeline,
            selected_entities=entity_list
        )
        
        create_redaction_log(
            db=db,
            user_id=current_user.id,
            input_type="pdf",
            source_name=file.filename,
            entity_count=entity_count
        )

        return StreamingResponse(
            pdf_file,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=redacted.pdf"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF Redaction Failed: {str(e)}"
        )

@router.post("/preview/pdf")
async def redact_pdf_preview_endpoint(
    request: Request,
    file: UploadFile = File(...),
    selected_entities: str = Form(None)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await file.read()
    
    try:
        pipeline = request.app.state.pii_pipeline
        
        entity_list = None
        if selected_entities is not None:
             try:
                parsed = json.loads(selected_entities)
                if isinstance(parsed, list) and parsed:
                    entity_list = parsed
             except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid selected_entities format")

        preview_text = redact_pdf_preview(
            file_bytes=file_bytes,
            pipeline=pipeline,
            selected_entities=entity_list
        )
        
        return {"preview_text": preview_text}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF Preview Failed: {str(e)}"
        )

# DOCX redaction
@router.post("/docx")
async def redact_docx_file(
    request: Request,
    file: UploadFile = File(...),
    selected_entities: str = Form(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not check_user_upload_limit(db, current_user.id):
        raise HTTPException(status_code=429, detail="Daily upload limit reached")

    file_bytes = await file.read()

    if not selected_entities:
        entity_list = None  
    else:
        parsed = json.loads(selected_entities)
        entity_list = parsed if parsed else None

    docx_file, entity_count = redact_docx_paragraphwise(
        original_doc_bytes=file_bytes,
        pipeline=request.app.state.pii_pipeline,
        selected_entities=entity_list
    )

    create_redaction_log(
        db=db,
        user_id=current_user.id,
        input_type="docx",
        source_name=file.filename,
        entity_count=entity_count
    )

    return StreamingResponse(
        docx_file,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": "attachment; filename=redacted.docx"
        }
    )

@router.post("/preview/docx")
async def redact_docx_preview_endpoint(
    request: Request,
    file: UploadFile = File(...),
    selected_entities: str = Form(None)
):
    file_bytes = await file.read()

    if not selected_entities:
        entity_list = None
    else:
        try:
            parsed = json.loads(selected_entities)
            entity_list = parsed if parsed else None
        except json.JSONDecodeError:
           raise HTTPException(status_code=400, detail="Invalid selected_entities format")

    try:
        preview_text = redact_docx_preview(
            original_doc_bytes=file_bytes,
            pipeline=request.app.state.pii_pipeline,
            selected_entities=entity_list
        )
        return {"preview_text": preview_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    if not check_user_upload_limit(db, current_user.id):
        raise HTTPException(status_code=429, detail="Daily upload limit reached")

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    file_bytes = await file.read()

    try:
        columns = json.loads(selected_columns)

        headers, redacted_rows, entity_count = extract_redacted_csv_data(
            file_bytes,
            columns
        )

        csv_file = create_redacted_csv(headers, redacted_rows)

        create_redaction_log(
            db=db,
            user_id=current_user.id,
            input_type="csv",
            source_name=file.filename,
            entity_count=entity_count,
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

@router.post("/preview/csv")
async def redact_csv_preview(
    file: UploadFile = File(...),
    selected_columns: str = Form(...)
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    file_bytes = await file.read()

    try:
        columns = json.loads(selected_columns)
        preview_data = get_redacted_csv_preview(file_bytes, columns)
        return preview_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/detect/entities")
async def detect_entities(
    request: Request,
    file: UploadFile = File(None),
    text: str = Form(None),
    current_user = Depends(get_current_user)
):
    try:
        content = ""
        
        if text:
            content = text
        elif file:
            filename = file.filename.lower()

            if not (filename.endswith(".pdf") or filename.endswith(".docx")):
                raise HTTPException(
                    status_code=400,
                    detail="Only PDF and DOCX files are supported"
                )

            file_bytes = await file.read()
            await file_size_validator(file_bytes)

            if filename.endswith(".pdf"):
                import fitz
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                for page in doc:
                    content += page.get_text()
            else:
                content = extract_text_from_docx(file_bytes)
        else:
            raise HTTPException(
                status_code=400,
                detail="Either text or file must be provided"
            )

        if not content.strip():
            raise HTTPException(
                status_code=400,
                detail="No readable text found"
            )

        pipeline = request.app.state.pii_pipeline
        _, entities = pipeline.run(content)

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

@router.get("/dashboard/user-stats", response_model=UserStats)
def get_stats(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        stats = get_user_stats(db, current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stats: {str(e)}"
        )
