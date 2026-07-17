import httpx
import os
from typing import Dict, Any

class VLLMClient:
    def __init__(self, api_base: str):
        self.api_base = api_base
        api_key = os.environ.get("VLLM_API_KEY", "NONE")
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def generate(self, prompt: str) -> Dict[str, Any]:
        with httpx.Client() as client:
            response = client.post(
                f"{self.api_base}/completions",
                json={"model": "default", "prompt": prompt},
                headers=self.headers
            )
            return response.json()
