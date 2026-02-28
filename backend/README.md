# 🛡️ Insurance PII Redaction API

A **FastAPI-based backend service** for detecting and redacting **Personally Identifiable Information (PII)** from unstructured insurance and healthcare text. The API is designed to be consumed by a **Next.js frontend** and focuses on clean API design, backend integration, and schema validation.

> ⚠️ **Note:** The core PII detection and anonymization logic was developed and provided by the **AI/ML team**. This project highlights backend engineering, API integration, and system orchestration.

---

## 🎯 Project Scope & Contributions

### ✅ Implemented by Web Development Team

* FastAPI application setup (`main.py`)
* API routing and endpoint design (`/api/redact`)
* Request and response schemas using **Pydantic**
* Integration of the AI/ML redaction pipeline into FastAPI
* CORS configuration for frontend communication (Next.js)
* Structured error handling and response formatting
* Swagger / OpenAPI testing and validation

### 🤖 Provided by AI/ML Team

* PII detection pipeline (GLiNER-based Named Entity Recognition)
* Regex-based entity detection
* Entity normalization and merging logic
* Presidio anonymization logic
* Core redaction pipeline orchestration

---

## 🚀 Features

* ✍️ Accepts raw text input
* 🔒 Returns redacted / anonymized text
* 🔍 Returns detected PII entities with:

  * Entity type
  * Character offsets
  * Confidence scores
* 🏥 Designed for **insurance and healthcare data privacy** use cases
* 📄 Auto-generated API documentation via FastAPI

---

## 🧠 Tech Stack

### Backend

* Python
* FastAPI
* Pydantic
* Uvicorn

### NLP / PII Detection

* GLiNER
* Presidio Anonymizer
* spaCy

### Frontend (Consumer)

* Next.js

---

## 📌 API Endpoint

### 🔐 Redact PII

```
POST /api/redact
```

#### Example Request

```json
{
  "text": "John Doe lives at 221B Baker Street and his policy number is 123-45-6789."
}
```

#### Example Response

```json
{
  "redacted_text": "***** lives at ***** and his policy number is *****.",
  "entities": [
    {
      "entity": "NAME",
      "start": 0,
      "end": 8,
      "confidence": 0.97
    }
  ]
}
```

---

## 🛠️ Running Locally

### 1️⃣ Create a Virtual Environment

```bash
python -m venv venv
```

### 2️⃣ Activate the Environment

```bash
venv\Scripts\activate   # Windows
# or
source venv/bin/activate # Linux / macOS
```

### 3️⃣ Start the Server

```bash
uvicorn app.main:app
```

The API will be available at:

```
http://127.0.0.1:8000
```

---

## 📖 API Documentation

Once the server is running:

* 📘 Swagger UI → `/docs`
* 📕 ReDoc → `/redoc`

These interfaces allow interactive testing and schema inspection.

---

## 📝 Notes

* Large NLP models are loaded **once at application startup**
* Auto-reload is avoided to prevent multiple model initializations
* CORS is enabled for seamless frontend-backend integration
* The primary focus of this project is **backend API integration**, not model training

---

## 📈 Future Enhancements

* 🔐 Authentication and authorization (JWT)
* 📊 Request logging and audit trails
* 🐳 Dockerization
* 🧪 Automated testing with pytest
* ☁️ Production deployment

---

## 📜 License

This project is licensed under the **MIT License**.

---

⭐ If you find this project useful, consider giving it a star!
