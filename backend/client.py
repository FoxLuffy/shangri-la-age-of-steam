import httpx
import os
from typing import Dict, Any, Optional

class VLLMClient:
    """
    Client for communicating with the vLLM inference server.
    """
    def __init__(
        self,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.api_base = api_base or os.getenv("VLLM_API_BASE", "http://localhost:8000/v1")
        self.model = model or os.getenv("VLLM_MODEL", "default")
        self.timeout = timeout
        api_key = os.environ.get("VLLM_API_KEY", "NONE")
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Generates text completion using the vLLM endpoint.
        """
        endpoint = f"{self.api_base}/completions"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            **kwargs
        }
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                endpoint,
                json=payload,
                headers=self.headers
            )
            return response.json()

