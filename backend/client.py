import httpx
from typing import Dict, Any

class VLLMClient:
    def __init__(self, api_base: str):
        self.api_base = api_base
        self.headers = {"Authorization": "Bearer-NONE"}

    def generate(self, prompt: str) -> Dict[str, Any]:
        with httpx.Client() as client:
            response = client.post(
                f"{self.api_base}/completions",
                json={"model": "default", "prompt": prompt},
                headers=self.headers
            )
            return response.json()
