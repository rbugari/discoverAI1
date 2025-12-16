import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
from ..config import settings

# --- Pydantic Models for Output Parsing ---

class DataEntity(BaseModel):
    name: str = Field(description="Name of the table, file, or API endpoint")
    type: str = Field(description="Type of entity: TABLE, FILE, API, DATABASE")
    schema_name: Optional[str] = Field(description="Schema name if available (e.g., 'dbo', 'public')")
    system: Optional[str] = Field(description="System hint (e.g., 'DataLake', 'CRM')")
    columns: Optional[List[str]] = Field(description="List of column names extracted from the code context, if available", default=[])

class AnalysisResult(BaseModel):
    file_path: Optional[str] = Field(description="Original file path")
    summary: str = Field(description="Concise summary of what the code does")
    inputs: List[DataEntity] = Field(description="List of data sources read by this code")
    outputs: List[DataEntity] = Field(description="List of data destinations written by this code")
    transformation_logic: Optional[str] = Field(description="Brief description of transformations applied")

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
        self.parser = JsonOutputParser(pydantic_object=AnalysisResult)
        
        # Load prompts from external files
        self.prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")
        
    def _load_prompt(self, filename: str) -> str:
        try:
            with open(os.path.join(self.prompts_dir, filename), "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            print(f"Error loading prompt {filename}: {e}")
            return ""

    def analyze_code(self, file_path: str, code_content: str, extension: str) -> AnalysisResult:
        print(f"Analyzing {file_path} with {settings.OPENROUTER_MODEL}...")
        
        # Escape curly braces in the prompt to prevent LangChain from interpreting them as variables
        format_instructions = self.parser.get_format_instructions().replace("{", "{{").replace("}", "}}")
        
        system_prompt = self._load_prompt("analysis_prompt.md")
        if not system_prompt:
             # Fallback if file load fails
             system_prompt = """You are a Senior Data Engineer specializing in Reverse Engineering.
             Your goal is to analyze source code (SQL, Python, ETL XMLs) and extract data lineage information.
             Identify what data is being read (inputs) and what data is being written (outputs).
             Ignore temporary variables or print statements. Focus on data movement.
             """
        
        user_prompt = f"""
        Analyze the following code file: '{{file_path}}'
        
        CODE CONTENT:
        ```
        {{code_content}} 
        ```
        (Code truncated if too long)
        
        Return a JSON object matching the requested schema.
        {format_instructions}
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt)
        ])
        
        chain = prompt | self.llm | self.parser
        
        try:
            # Pass variables to the chain
            result = chain.invoke({"file_path": file_path, "code_content": code_content[:15000]})
            # Ensure file_path is set in the result
            if isinstance(result, dict):
                 result['file_path'] = file_path
                 return AnalysisResult(**result)
            return result
        except Exception as e:
            print(f"LLM Analysis Failed for {file_path}: {e}")
            # Return empty result on failure
            return AnalysisResult(
                file_path=file_path,
                summary="Analysis Failed",
                inputs=[],
                outputs=[]
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
