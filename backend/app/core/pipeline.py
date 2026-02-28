# pipeline.py
from typing import Tuple, List

from .config import PRESIDIO_OPERATORS, NAME_FALLBACK_RE, POSSESSIVE_NAME_RE
from app.services.detector import (
    GLiNERDetector,
    LabelMapper,
    regex_detect,
    merge_person_entities,
    normalize_addresses,
    PIIEntity,
)
from app.services.anonymizer import PresidioWrapper


def final_name_sweep(text: str) -> str:
    def repl(m):
        whole = m.group(0)
        name = m.group(2)
        return whole.replace(name, "[NAME]")

    return NAME_FALLBACK_RE.sub(repl, text)


def possessive_name_sweep(text: str) -> str:
    def repl(m):
        return "[NAME]'s"
    return POSSESSIVE_NAME_RE.sub(repl, text)


class PIIPipeline:
    def __init__(self):
        self.detector = GLiNERDetector()
        self.mapper = LabelMapper()
        self.anonymizer = PresidioWrapper()

    def run(self, text: str) -> Tuple[str, List[PIIEntity]]:
        raw = self.detector.detect(text)

        entities: List[PIIEntity] = [
            PIIEntity(
                entity_type=self.mapper.normalize(e["label"]),
                start=int(e["start"]),
                end=int(e["end"]),
                score=float(e["score"]),
                text=text[int(e["start"]):int(e["end"])],
            )
            for e in raw
        ]

        regex_entities = regex_detect(text)
        for e in regex_entities:
            e.entity_type = self.mapper.normalize(e.entity_type)
        entities.extend(regex_entities)

        entities = merge_person_entities(text, entities)
        entities = normalize_addresses(text, entities)

        anonymized = self.anonymizer.anonymize(
            text=text,
            entities=entities,
            operators=PRESIDIO_OPERATORS,
        )

        anonymized = final_name_sweep(anonymized)
        anonymized = possessive_name_sweep(anonymized)

        return anonymized, entities
