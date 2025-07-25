import requests
import json
from typing import List, Dict, Any, Optional

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "gemma3"):
        self.base_url = base_url
        self.model = model
        self.chat_endpoint = f"{base_url}/api/chat"
    
    def generate_content(self, messages: List[Dict[str, str]]) -> 'OllamaResponse':
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        try:
            response = requests.post(self.chat_endpoint, json=payload)
            response.raise_for_status()
            result = response.json()
            
            content = result.get("message", {}).get("content", "")
            return OllamaResponse(content)

        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        try:
            response = self.generate_content(messages)
            return response.text
        except Exception as e:
            raise Exception(f"Chat error: {str(e)}")

class OllamaResponse:
    def __init__(self, text: str):
        self.text = text
        self.content = text  # For compatibility