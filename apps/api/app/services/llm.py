import json
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
from ..config import settings
from ..models.extraction import ExtractionResult

# --- Service ---

import os

class LLMService:
    def __init__(self):
        self.llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
            model_name=settings.OPENROUTER_MODEL,
            temperature=0
        )
        # For embeddings, we usually need a direct OpenAI key or a provider that supports it
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-small"
        )
        self.parser = JsonOutputParser(pydantic_object=ExtractionResult)
        
    def get_embeddings(self, text: str) -> List[float]:
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            print(f"Embedding generation failed: {e}")
            return []
        
        # Load prompts from external files
        self.prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")
        
    def _load_prompt(self, filename: str) -> str:
        try:
            with open(os.path.join(self.prompts_dir, filename), "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            print(f"Error loading prompt {filename}: {e}")
            return ""

    def analyze_code(self, file_path: str, code_content: str, extension: str) -> ExtractionResult:
        print(f"Analyzing {file_path} with {settings.OPENROUTER_MODEL}...")
        
        system_prompt = self._load_prompt("analysis_prompt.md")
        if not system_prompt:
             # Fallback
             system_prompt = "You are a Senior Data Engineer. Extract data lineage."
        
        # We pass format_instructions as a variable to avoid f-string escaping issues with JSON schema
        format_instructions = self.parser.get_format_instructions()
        
        user_prompt_template = """
        Analyze the following code file: '{file_path}'
        
        CODE CONTENT:
        ```
        {code_content} 
        ```
        (Code truncated if too long)
        
        Return a JSON object matching the requested schema.
        {format_instructions}
        """
        
        # Use SystemMessage for system prompt to avoid template parsing errors with JSON braces
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            ("user", user_prompt_template)
        ])
        
        chain = prompt | self.llm | self.parser
        
        try:
            # Pass variables to the chain
            result = chain.invoke({
                "file_path": file_path, 
                "code_content": code_content[:15000],
                "format_instructions": format_instructions
            })
            
            # Ensure meta matches
            if isinstance(result, dict):
                 if "meta" not in result: result["meta"] = {}
                 result["meta"]["source_file"] = file_path
                 return ExtractionResult(**result)
            return result
        except Exception as e:
            print(f"LLM Analysis Failed for {file_path}: {e}")
            # Return empty result on failure
            return ExtractionResult(
                meta={"source_file": file_path, "extractor_id": "error"},
                nodes=[],
                edges=[],
                evidences=[]
            )

    def chat_with_graph(self, graph_context: dict, question: str) -> str:
        """
        Answers a user question based on the provided graph context.
        """
        system_prompt = self._load_prompt("chat_prompt.md")
        if not system_prompt:
             system_prompt = "You are a Data Architect Assistant."
        
        # Simplify graph for context window
        nodes_summary = [f"{n['data']['type']}: {n['data']['label']}" for n in graph_context.get('nodes', [])]
        edges_summary = [f"{e['source']} -> {e['label']} -> {e['target']}" for e in graph_context.get('edges', [])]
        
        context_str = f"""
        NODES:
        {json.dumps(nodes_summary, indent=2)}
        
        RELATIONSHIPS:
        {json.dumps(edges_summary, indent=2)}
        """
        
        user_prompt = f"""
        CONTEXT:
        {context_str}
        
        QUESTION:
        {question}
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt)
        ])
        
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({})
            return response.content
        except Exception as e:
            print(f"Chat failed: {e}")
            return "I apologize, but I encountered an error while processing your request."

