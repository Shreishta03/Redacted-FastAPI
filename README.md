Insurance PII Redaction API

A FastAPI-based backend service for detecting and redacting Personally Identifiable Information (PII) from unstructured insurance and healthcare text. The API is designed to be consumed by a Next.js frontend.

This project focuses on API design, backend integration, and schema validation, while the core PII detection and anonymization logic was provided by an AI/ML team.

Project Scope and Contributions

Implemented by Me
- FastAPI application setup (main.py)
- API routing and endpoint design (/api/redact)
- Request and response schemas using Pydantic
- Integration of the AI pipeline into FastAPI
- CORS configuration for frontend communication
- Error handling and response formatting
- Swagger/OpenAPI testing and validation

Provided by AI/ML Team
- PII detection pipeline (GLiNER-based NER)
- Regex-based entity detection
- Entity normalization and merging logic
- Presidio anonymization logic
- Core pipeline orchestration

Features
- Accepts raw text input
- Returns redacted/anonymized text
- Returns detected PII entities with offsets and confidence scores
- Designed for insurance and healthcare data privacy use cases

Tech Stack
- Python
- FastAPI
- Pydantic
- GLiNER
- Presidio Anonymizer
- spaCy
- Uvicorn
- Frontend: Next.js


API Endpoint
POST /api/redact

Running Locally
python -m venv venv
venv\Scripts\activate
uvicorn app.main:app

Notes
- Large NLP models are loaded once at startup
- Auto-reload is avoided to prevent multiple model loads
- CORS is enabled for frontend integration
- Focus of this project is backend API integration rather than model training

