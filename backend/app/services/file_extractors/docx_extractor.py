from docx import Document
from io import BytesIO

def extract_text_from_docx(file_bytes: bytes) -> str:
    document = Document(BytesIO(file_bytes))
    paragraphs = []
    for para in document.paragraphs:
        if para.text:
            paragraphs.append(para.text)

    return "\n".join(paragraphs)