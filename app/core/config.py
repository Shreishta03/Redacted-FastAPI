# config.py
import os
import re
from presidio_anonymizer.entities import OperatorConfig


# -------------------------------
# Model / runtime settings
# -------------------------------
GLINER_MODEL_PATH = os.getenv("PII_MODEL_PATH", "nvidia/gliner-PII")
GLINER_SCORE_THRESHOLD = float(os.getenv("PII_SCORE_THRESHOLD", "0.35"))

# Comma-separated label list, override if you fine-tune
GLINER_LABELS = [
    x.strip()
    for x in os.getenv(
        "PII_LABELS",
        "person,email,phone number,fax number,credit card,"
        "bank account,ssn,organization,address,location,date,"
        "date of birth,medical record number",
    ).split(",")
]


# -------------------------------
# Regex patterns (configurable)
# -------------------------------
REGEX_PATTERNS = {
    "US_SSN": re.compile(os.getenv("PATTERN_US_SSN", r"\*{3}-\*{2}-\d{4}")),
    "CREDIT_CARD": re.compile(os.getenv("PATTERN_CREDIT_CARD", r"\*{4}\s?\d{4}")),

    "FAX_NUMBER": re.compile(
        os.getenv("PATTERN_FAX_NUMBER", r"fax[:\s]*\+?\d[\d\s().-]{6,}\d"),
        re.I,
    ),

    "PATIENT_NAME": re.compile(
        os.getenv(
            "PATTERN_PATIENT_NAME",
            r"(patient name|doctor name)[:\s]*[A-Z][A-Za-zΛ.\s]{2,}",
        ),
        re.I,
    ),

    "ROLE_NAME": re.compile(
        os.getenv(
            "PATTERN_ROLE_NAME",
            r"(provider|primary care provider|guarantor|reviewed by|signed by|physician|consultant)"
            r"[:\s]+[A-Z][A-Za-z.\s]{2,}",
        ),
        re.I,
    ),

    "TRAILING_NAME_WITH_CRED": re.compile(
        os.getenv(
            "PATTERN_TRAILING_NAME_WITH_CRED",
            r"\b[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z.]+){0,3}\s*,\s*"
            r"(MD|DO|NP|PA|PT|RN|PharmD)\b\.?",
        ),
        re.I,
    ),

    "BULLET_PROVIDER": re.compile(
        os.getenv(
            "PATTERN_BULLET_PROVIDER",
            r"(?:Provider|Guarantor)\s*\*{0,2}:?\*{0,2}\s*"
            r"([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z.]+){0,3})",
        ),
        re.I,
    ),
}

NAME_FALLBACK_RE = re.compile(
    os.getenv(
        "PATTERN_NAME_FALLBACK",
        r"(provider|primary care provider|guarantor|np|pt|md|do|rn|pa)\b"
        r"[^.\n]*\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z.]+){0,3})",
    ),
    re.I,
)

POSSESSIVE_NAME_RE = re.compile(
    os.getenv(
        "PATTERN_POSSESSIVE_NAME",
        r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z.]+){0,3})'s\b",
    )
)


# -------------------------------
# Presidio operator configuration
# -------------------------------
PRESIDIO_OPERATORS = {
    "PERSON": OperatorConfig("replace", {"new_value": "[NAME]"}),
    "ADDRESS": OperatorConfig("replace", {"new_value": "[ADDRESS]"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[PHONE]"}),
    "FAX_NUMBER": OperatorConfig("replace", {"new_value": "[FAX]"}),
    "US_SSN": OperatorConfig("replace", {"new_value": "[SSN]"}),
    "CREDIT_CARD": OperatorConfig("replace", {"new_value": "[CARD]"}),
    "BANK_ACCOUNT": OperatorConfig("replace", {"new_value": "[BANK]"}),
    "DATE_TIME": OperatorConfig("replace", {"new_value": "[DATE]"}),
    "ORGANIZATION": OperatorConfig("replace", {"new_value": "[ORG]"}),
    "MEDICAL_RECORD_NUMBER": OperatorConfig("replace", {"new_value": "[MRN]"}),
    "DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"}),
}

#WebDev
#Plain text length config
MAX_PLAIN_TEXT_LENGTH = int(
    os.getenv("MAX_PLAIN_TEXT_LENGTH", "5000")
)