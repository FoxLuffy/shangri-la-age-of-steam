import httpx
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class VLLMClient:
    def __init__(self, api_base: Optional[str] = None):
        if not api_base:
            api_base = os.environ.get("VLLM_SERVER_URL") or os.environ.get("VLLM_API_BASE", "http://localhost:8000/v1")
        self.api_base = api_base.rstrip('/')
        api_key = os.environ.get("VLLM_API_KEY", "NONE")
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def generate(self, prompt: str) -> Dict[str, Any]:
        endpoint = f"{self.api_base}/completions" if not self.api_base.endswith("/completions") else self.api_base
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.post(
                    endpoint,
                    json={"model": "default", "prompt": prompt},
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
