import httpx
import os
import logging
from typing import Dict, Any, Optional
from backend.prompt_utils import get_dynamic_narration

logger = logging.getLogger(__name__)

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
        if not api_base:
            api_base = os.environ.get("VLLM_SERVER_URL") or os.environ.get("VLLM_API_BASE", "http://localhost:8000/v1")
        self.api_base = api_base.rstrip('/')
        self.model = model or os.environ.get("VLLM_MODEL", "gemma-4")
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
        endpoint = f"{self.api_base}/chat/completions" if not self.api_base.endswith("/chat/completions") else self.api_base
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            **kwargs
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    endpoint,
                    json=payload,
                    headers=self.headers
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"VLLM returned status code {response.status_code}")
                    raise RuntimeError(f"VLLM server returned non-200 status code: {response.status_code}")
        except Exception as e:
            logger.error(f"VLLM endpoint unavailable ({e})")
            raise RuntimeError(f"VLLM endpoint unavailable: {e}")

    def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs: Any
    ):
        """
        Generates text completion using the vLLM endpoint and yields chunks.
        """
        endpoint = f"{self.api_base}/chat/completions" if not self.api_base.endswith("/chat/completions") else self.api_base
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": True,
            **kwargs
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream("POST", endpoint, json=payload, headers=self.headers) as response:
                    if response.status_code != 200:
                        logger.error(f"VLLM returned status code {response.status_code}")
                        raise RuntimeError(f"VLLM server returned non-200 status code: {response.status_code}")

                    for line in response.iter_lines():
                        line = line.decode('utf-8') if isinstance(line, bytes) else line
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            if data_str:
                                import json
                                try:
                                    yield json.loads(data_str)
                                except Exception:
                                    pass
        except Exception as e:
            logger.error(f"VLLM endpoint unavailable ({e})")
            raise RuntimeError(f"VLLM endpoint unavailable: {e}")
