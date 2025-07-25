import openai
from typing import List, Dict

class OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def chat(self, messages: List[Dict]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content


    def generate_content(self, messages: List[Dict]) -> object:
        class OpenAIResponse:
            def __init__(self, text: str):
                self.text = text
        
        content = self.chat(messages)
        return OpenAIResponse(content)
