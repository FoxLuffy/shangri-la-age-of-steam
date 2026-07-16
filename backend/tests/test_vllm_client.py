import pytest
from unittest.mock import Mock, patch
from backend.client import VLLMClient

def test_vllm_connection():
    # Mocking the httpx.Client.post method to avoid actual networking
    with patch("httpx.Client.post") as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"text": "Mocked response"}]}
        mock_post.return_value = mock_response
        
        client = VLLMClient(api_base="http://localhost:8000/v1")
        response = client.generate("Hello")
        assert "choices" in response
        assert response["choices"][0]["text"] == "Mocked response"

