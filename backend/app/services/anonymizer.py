# anonymizer.py
from typing import List, Dict

from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig, RecognizerResult

from .detector import PIIEntity


class PresidioWrapper:
    def __init__(self):
        self.engine = AnonymizerEngine()

    def anonymize(
        self,
        text: str,
        entities: List[PIIEntity],
        operators: Dict[str, OperatorConfig],
    ) -> str:
        results = [
            RecognizerResult(
                entity_type=e.entity_type,
                start=e.start,
                end=e.end,
                score=e.score,
            )
            for e in entities
        ]
        return self.engine.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators,
        ).text
