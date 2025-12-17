import os
from .base import BaseExtractor
from .llm import LLMExtractor
from .regex import RegexExtractor
from .sql_glot import SqlGlotExtractor

class ExtractorRegistry:
    def __init__(self):
        self.llm_extractor = LLMExtractor()
        self.regex_extractor = RegexExtractor()
        self.sql_extractor = SqlGlotExtractor()
        
    def get_extractor(self, file_path: str) -> BaseExtractor:
        """
        Returns the appropriate extractor for the file.
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.sql':
            return self.sql_extractor
            
        # For other files (py, xml, etc), we still use LLM for now as it's more versatile 
        # until we implement AST parsers for Python.
        return self.llm_extractor

    def extract(self, file_path: str, content: str):
        extractor = self.get_extractor(file_path)
        return extractor.extract(file_path, content)
