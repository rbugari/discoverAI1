import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Mode
    GRAPH_MODE: str = "MOCK" 

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    
    # Supabase (Required for Auth & DB)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = "" # Add Service Role Key for Admin operations
    
    # OpenRouter / OpenAI
    OPENAI_API_KEY: str = ""
    OPENROUTER_MODEL: str = "deepseek/deepseek-v3.2"
    
    # Storage
    UPLOAD_DIR: str = os.path.join(os.getcwd(), "temp_uploads")

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env"),
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)