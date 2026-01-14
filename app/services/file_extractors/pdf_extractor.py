from PyPDF2 import PdfReader
from io import BytesIO

def extract_text_from_pdf(file_bytes: bytes) -> str:
    
    #file_bytes: Raw bytes of the uploaded PDF
    reader = PdfReader(BytesIO(file_bytes))
    text_chunks = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_chunks.append(page_text)
        
    #return: Extracted text as string
    return "\n".join(text_chunks)