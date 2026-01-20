from docx import Document
import io

def create_redacted_docx(redacted_text: str):
    doc = Document()
    for line in redacted_text.split("\n"):
        doc.add_paragraph(line)

    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output
