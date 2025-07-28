"""Anonymizer class for pseudonymizing Personally Identifiable Information (PII) using Presidio.
This class identifies and pseudonymizes PII entities in the text using Presidio's analyzer engine.
It stores mappings to allow reversible transformations.
"""

import uuid
from typing import Dict, List

from presidio_analyzer import AnalyzerEngineProvider, RecognizerResult

from datu.app_config import AnonymizationConfig


class PiiAnonymizer:
    """A class to pseudonymize and deanonymize PII in text using Presidio.

    Args:
        language (str): The language of the text. Default is "en".

    Attributes:
        language (str): The language of the text.
        supported_entities (list): List of PII entities supported for pseudonymization.
        analyzer (AnalyzerEngine): Presidio's analyzer engine.
        pseudonym_map (dict): Map of pseudonym tokens to original PII values.
    """

    def __init__(self):
        config = AnonymizationConfig()
        self.language = config.supported_language or "en"
        self.provider = AnalyzerEngineProvider(analyzer_engine_conf_file=config.engine_conf_file)
        self.analyzer = self.provider.create_engine()
        self.pseudonym_map: Dict[str, str] = {}

    def anonymize(self, text: str) -> str:
        """Pseudonymizes PII entities in the given text.

        Args:
            text (str): The input text containing PII.

        Returns:
            str: The pseudonymized text with PII entities replaced by tokens.
        """
        results: List[RecognizerResult] = self.analyzer.analyze(
            text=text,
            language=self.language,
        )

        # Sort by start ascending, length descending
        sorted_results = sorted(results, key=lambda r: (r.start, -(r.end - r.start)))

        # Deduplicate overlapping results
        non_overlapping = []
        last_end = -1
        for r in sorted_results:
            if r.start >= last_end:  # No overlap
                non_overlapping.append(r)
                last_end = r.end

        pseudonymized_text = text
        for r in sorted(non_overlapping, key=lambda r: r.start, reverse=True):
            value = text[r.start : r.end]
            token = self._generate_token(r.entity_type)
            self.pseudonym_map[token] = value
            pseudonymized_text = pseudonymized_text[: r.start] + token + pseudonymized_text[r.end :]

        return pseudonymized_text

    def deanonymize(self, text: str) -> str:
        """Replaces pseudonym tokens in text with original PII values.

        Args:
            text (str): The pseudonymized text.

        Returns:
            str: The restored original text.
        """
        for token, original in self.pseudonym_map.items():
            text = text.replace(token, original)
        return text

    def _generate_token(self, entity_type: str) -> str:
        """Generate a unique pseudonym token."""
        return f"<{entity_type}_{uuid.uuid4().hex[:8]}>"
