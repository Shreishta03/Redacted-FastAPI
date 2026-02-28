# detector.py
import logging
from dataclasses import dataclass
from typing import List, Dict, Any

from gliner import GLiNER
from app.core.config import GLINER_MODEL_PATH, GLINER_SCORE_THRESHOLD, GLINER_LABELS, REGEX_PATTERNS

logger = logging.getLogger(__name__)


@dataclass
class PIIEntity:
    entity_type: str
    start: int
    end: int
    score: float
    text: str


class LabelMapper:
    @staticmethod
    def normalize(label: str) -> str:
        l = label.lower()

        if "role_name" in l or "patient_name" in l:
            return "PERSON"
        if "trailing_name_with_cred" in l or "bullet_provider" in l:
            return "PERSON"

        if "person" in l or "name" in l:
            return "PERSON"
        if "email" in l:
            return "EMAIL_ADDRESS"
        if "phone" in l:
            return "PHONE_NUMBER"
        if "fax" in l:
            return "FAX_NUMBER"
        if "ssn" in l:
            return "US_SSN"
        if "credit" in l:
            return "CREDIT_CARD"
        if "bank" in l:
            return "BANK_ACCOUNT"
        if "address" in l or "location" in l:
            return "ADDRESS"
        if "date of birth" in l:
            return "DATE_TIME"
        if l == "date":
            return "DATE_TIME"
        if "organization" in l:
            return "ORGANIZATION"
        if "medical record number" in l or l == "mrn":
            return "MEDICAL_RECORD_NUMBER"

        return label.upper()


class GLiNERDetector:
    def __init__(self):
        logger.info("Loading GLiNER model from %s", GLINER_MODEL_PATH)
        self.model = GLiNER.from_pretrained(GLINER_MODEL_PATH)
        self.score_threshold = GLINER_SCORE_THRESHOLD
        self.labels = GLINER_LABELS

    def detect(self, text: str) -> List[Dict[str, Any]]:
        if not text.strip():
            return []
        return self.model.predict_entities(
            text=text,
            labels=self.labels,
            threshold=self.score_threshold,
        )


def regex_detect(text: str) -> List[PIIEntity]:
    entities: List[PIIEntity] = []
    for etype, pattern in REGEX_PATTERNS.items():
        for m in pattern.finditer(text):
            if etype == "BULLET_PROVIDER":
                start, end = m.start(1), m.end(1)
            else:
                start, end = m.start(), m.end()
            entities.append(
                PIIEntity(
                    entity_type=etype,
                    start=start,
                    end=end,
                    score=1.0,
                    text=text[start:end],
                )
            )
    return entities


def merge_person_entities(text: str, entities: List[PIIEntity]) -> List[PIIEntity]:
    entities = sorted(entities, key=lambda e: e.start)
    merged: List[PIIEntity] = []
    i = 0

    while i < len(entities):
        cur = entities[i]
        if cur.entity_type == "PERSON":
            j = i + 1
            end = cur.end
            score = cur.score
            while (
                j < len(entities)
                and entities[j].entity_type == "PERSON"
                and entities[j].start - end <= 2
            ):
                end = entities[j].end
                score = max(score, entities[j].score)
                j += 1

            merged.append(
                PIIEntity(
                    entity_type="PERSON",
                    start=cur.start,
                    end=end,
                    score=score,
                    text=text[cur.start:end],
                )
            )
            i = j
        else:
            merged.append(cur)
            i += 1

    return merged


def normalize_addresses(text: str, entities: List[PIIEntity]) -> List[PIIEntity]:
    addr = [e for e in entities if e.entity_type == "ADDRESS"]
    others = [e for e in entities if e.entity_type != "ADDRESS"]

    if not addr:
        return entities

    start = min(e.start for e in addr)
    end = max(e.end for e in addr)

    others.append(
        PIIEntity(
            entity_type="ADDRESS",
            start=start,
            end=end,
            score=max(e.score for e in addr),
            text=text[start:end],
        )
    )
    return others
