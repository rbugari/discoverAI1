import os
from .base import BaseExtractor
from ...models.extraction import ExtractionResult
from ..llm import LLMService

class LLMExtractor(BaseExtractor):
    def __init__(self):
        self.llm_service = LLMService()

    def extract(self, file_path: str, content: str) -> ExtractionResult:
        extension = os.path.splitext(file_path)[1].lower()
        # Delegate to the existing LLMService
        return self.llm_service.analyze_code(file_path, content, extension)
