"""
Adaptador LLM para ActionRunner - Integración con Groq y OpenRouter
"""
import os
import json
import time
from typing import Dict, Any, Optional

from ..config import settings

class LLMAdapter:
    """
    Adaptador unificado para llamadas a LLMs (Groq, OpenRouter)
    """
    
    def __init__(self):
        # Inicialización perezosa de clientes
        self.groq_client = None
        self.openai_client = None # Para OpenRouter (usa interfaz OpenAI)
        
    def _get_groq_client(self):
        if not self.groq_client:
            from groq import Groq
            if not settings.GROQ_API_KEY:
                print("[LLM ADAPTER] WARNING: GROQ_API_KEY not set")
            self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        return self.groq_client

    def _get_openrouter_client(self):
        if not self.openai_client:
            from openai import OpenAI
            self.openai_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.OPENAI_API_KEY,
            )
        return self.openai_client

    def call_model(
        self,
        model: str,
        messages: list,
        temperature: float = 0.1,
        max_tokens: int = 1800,
        provider: str = None,
        json_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Llamada unificada a LLM. Despacha al proveedor correcto.
        """
        # --- MULTI-MODAL NORMALIZATION ---
        # Ensure 'messages' is in the format expected by the chosen provider.
        # OpenAI/OpenRouter support list of parts in 'content'. Groq varies.
        
        if provider is None:
            # AUTO-DETECT: If model has a slash (e.g. google/gemini), it's likely an OpenRouter model
            if "/" in model:
                provider = "openrouter"
            else:
                provider = settings.LLM_PROVIDER
        
        if provider == "groq":
            return self.call_groq(model, messages, temperature, max_tokens, json_mode=json_mode)
        else:
            return self.call_openrouter(model, messages, temperature, max_tokens, json_mode=json_mode)

    def call_groq(
        self,
        model: str,
        messages: list,
        temperature: float = 0.1,
        max_tokens: int = 1800,
        json_mode: bool = False
    ) -> Dict[str, Any]:
        """Llamada a Groq"""
        try:
            client = self._get_groq_client()
            
            # NOTE: Groq specifically might NOT support images in all models yet.
            # We assume 'messages' are already pre-formatted or handled.
            
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
                response_format={"type": "json_object"} if json_mode else None
            )
            
            content = completion.choices[0].message.content
            
            usage = completion.usage
            tokens_in = usage.prompt_tokens if usage else 0
            tokens_out = usage.completion_tokens if usage else 0
            
            return {
                "success": True,
                "content": content,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "provider": "groq"
            }
            
        except Exception as e:
            print(f"[LLM ADAPTER] Groq Error: {e}")
            return {
                "success": False,
                "error": str(e),
                "tokens_in": 0,
                "tokens_out": 0
            }

    def call_openrouter(
        self,
        model: str,
        messages: list,
        temperature: float = 0.1,
        max_tokens: int = 2500, # Vision tasks often need more tokens for output
        json_mode: bool = False
    ) -> Dict[str, Any]:
        """Llamada a OpenRouter (soporta Multi-modal nativamente si el modelo lo permite)"""
        max_retries = 3
        retry_delay = 5 # seconds
        
        for attempt in range(max_retries):
            try:
                client = self._get_openrouter_client()
                
                completion = client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": "https://discoveria.app", 
                        "X-Title": "DiscoverIA",
                    },
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"} if json_mode else None
                )
                
                content = completion.choices[0].message.content
                usage = completion.usage
                
                return {
                    "success": True,
                    "content": content,
                    "tokens_in": usage.prompt_tokens if usage else 0,
                    "tokens_out": usage.completion_tokens if usage else 0,
                    "provider": "openrouter"
                }
                    
            except Exception as e:
                error_str = str(e)
                if "429" in error_str and attempt < max_retries - 1:
                    print(f"[LLM ADAPTER] Rate limit (429) hit. Retrying in {retry_delay}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2 
                    continue
                    
                print(f"[LLM ADAPTER] OpenRouter Error: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "tokens_in": 0,
                    "tokens_out": 0
                }

# Crear instancia global
_llm_adapter = None

def get_llm_adapter() -> LLMAdapter:
    """Obtiene instancia singleton del adaptador"""
    global _llm_adapter
    if _llm_adapter is None:
        _llm_adapter = LLMAdapter()
    return _llm_adapter
