import httpx
import os
import logging
from typing import Dict, Any, Optional

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
        endpoint = f"{self.api_base}/completions" if not self.api_base.endswith("/completions") else self.api_base
        payload = {
            "model": self.model,
            "prompt": prompt,
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
                    logger.warning(f"VLLM returned status code {response.status_code}")
        except Exception as e:
            logger.info(f"VLLM endpoint unavailable ({e}). Using mock narrative engine response.")

        # Fallback response for offline / dev mode
        return {
            "choices": [{
                "text": (
                    f"[Narration]\nThe hissed discharge of copper steam pipes echoes as your action unfolds. "
                    f"The ambient atmosphere thickens with the scent of coal smoke and oil.\n\n"
                    f"[StateUpdates]\n{{\"location_id\": \"1\"}}"
                )
            }],
            "text": (
                f"[Narration]\nThe hissed discharge of copper steam pipes echoes as your action unfolds. "
                f"The ambient atmosphere thickens with the scent of coal smoke and oil.\n\n"
                f"[StateUpdates]\n{{\"location_id\": \"1\"}}"
            ),
            "state_updates": {"location_id": "1"},
            "events": []
        }

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
        endpoint = f"{self.api_base}/completions" if not self.api_base.endswith("/completions") else self.api_base
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": True,
            **kwargs
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream("POST", endpoint, json=payload, headers=self.headers) as response:
                    if response.status_code == 200:
                        for line in response.iter_lines():
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
                    else:
                        logger.warning(f"VLLM returned status code {response.status_code}")
                        return
        except Exception as e:
            logger.info(f"VLLM endpoint unavailable ({e}). Using mock narrative engine response stream.")

        # Fallback response stream
        fallback_text = (
            f"[Narration]\nThe hissed discharge of copper steam pipes echoes as your action unfolds. "
            f"The ambient atmosphere thickens with the scent of coal smoke and oil.\n\n"
            f"[StateUpdates]\n{{\"location_id\": \"1\"}}"
        )
        import time
        # Yield words to simulate streaming
        words = fallback_text.split(" ")
        for i, word in enumerate(words):
            space = " " if i > 0 else ""
            yield {"choices": [{"text": space + word}]}
            time.sleep(0.05)
