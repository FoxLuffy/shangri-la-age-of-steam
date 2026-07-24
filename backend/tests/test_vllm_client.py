from unittest.mock import Mock, patch

import pytest
from backend.client import VLLMClient


@pytest.fixture
def vllm_client():
    return VLLMClient(api_base="http://localhost:8000/v1")


def test_vllm_client_init(vllm_client):
    assert vllm_client.api_base == "http://localhost:8000/v1"
    assert vllm_client.model == "gemma-4"


@patch("httpx.Client.post")
def test_vllm_client_generate_success(mock_post, vllm_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"choices": [{"text": "Hello, world!", "index": 0, "finish_reason": "stop"}]}
    mock_post.return_value = mock_response

    result = vllm_client.generate(prompt="Hello", max_tokens=10)
    assert result["choices"][0]["text"] == "Hello, world!"


@patch("httpx.Client.post")
def test_vllm_client_generate_failure(mock_post, vllm_client):
    mock_response = Mock()
    mock_response.status_code = 500
    mock_post.return_value = mock_response

    with pytest.raises(RuntimeError, match="VLLM server returned non-200 status code: 500"):
        vllm_client.generate(prompt="Hello")


@patch("httpx.Client.post")
def test_vllm_client_generate_exception(mock_post, vllm_client):
    mock_post.side_effect = Exception("Connection refused")

    with pytest.raises(RuntimeError, match="VLLM endpoint unavailable: Connection refused"):
        vllm_client.generate(prompt="Hello")


@patch("httpx.Client.stream")
def test_vllm_client_generate_stream_success(mock_stream, vllm_client):
    mock_response = Mock()
    mock_response.status_code = 200

    # Simulate lines from stream
    lines = [
        b'data: {"choices": [{"delta": {"delta": {"token": "Hello"}}}]}\n',
        b'data: {"choices": [{"delta": {"delta": {"token": " world"}}}]}\n',
        b"data: [DONE]\n",
    ]

    def mock_iter_lines():
        for line in lines:
            yield line

    mock_response.iter_lines.side_effect = mock_iter_lines
    mock_stream.return_value.__enter__.return_value = mock_response

    results = list(vllm_client.generate_stream(prompt="Hello"))
    assert len(results) == 2
    assert "Hello" in results[0]["choices"][0]["delta"]["delta"]["token"]
    assert " world" in results[1]["choices"][0]["delta"]["delta"]["token"]


@patch("httpx.Client.stream")
def test_vllm_client_generate_stream_failure(mock_stream, vllm_client):
    mock_response = Mock()
    mock_response.status_code = 500
    mock_stream.return_value.__enter__.return_value = mock_response

    with pytest.raises(RuntimeError, match="VLLM server returned non-200 status code: 500"):
        list(vllm_client.generate_stream(prompt="Hello"))
