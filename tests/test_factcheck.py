import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'services', 'factcheck_service')))

from main import app, startup_event

client = TestClient(app)

# We mock the RAGPipeline so we don't load huge models during testing
@pytest.fixture(autouse=True)
def run_startup():
    with patch('main.RAGPipeline') as MockPipeline:
        mock_instance = MockPipeline.return_value
        mock_instance.factcheck.return_value = {
            "verdict": "false",
            "evidence": "Mocked evidence.",
            "confidence": 0.85
        }
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(startup_event())

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["pipeline_ready"] is True

def test_factcheck_valid_claim():
    response = client.post("/factcheck", json={"claim": "The sky is green."})
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "false"
    assert "evidence" in data
    assert data["confidence"] == 0.85

def test_factcheck_empty_claim():
    response = client.post("/factcheck", json={"claim": "   "})
    assert response.status_code == 400
