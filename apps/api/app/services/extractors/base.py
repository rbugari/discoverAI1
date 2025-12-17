from abc import ABC, abstractmethod
from ...models.extraction import ExtractionResult

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: str, content: str) -> ExtractionResult:
        """
        Analyzes code content and returns an ExtractionResult.
        """
        pass
