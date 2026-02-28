from app.core.config import MAX_UPLOAD_SIZE_BYTES, MAX_UPLOAD_SIZE_MB
from fastapi import HTTPException, UploadFile

async def file_size_validator(file_bytes: bytes):
    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds {MAX_UPLOAD_SIZE_MB} MB limit"
        )
    
