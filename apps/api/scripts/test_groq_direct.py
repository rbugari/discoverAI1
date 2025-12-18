#!/usr/bin/env python3
import sys
import os
from pathlib import Path
from groq import Groq

# Añadir path para importar config
sys.path.append(str(Path(__file__).parent.parent))
from app.config import settings

def test_groq():
    print(f"Testing Groq API Key: {settings.GROQ_API_KEY[:10]}...")
    
    client = Groq(api_key=settings.GROQ_API_KEY)
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Explain quantum computing in 10 words."}
            ],
            temperature=0.1,
            max_tokens=100
        )
        
        print("\n✅ Success!")
        print(f"Response: {completion.choices[0].message.content}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_groq()