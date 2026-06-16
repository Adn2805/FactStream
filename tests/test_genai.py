import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'services', 'genai_service')))

from main import app, startup_event

client = TestClient(app)

@pytest.fixture(autouse=True)
def run_startup():
    with patch('main.LLMEngine') as MockEngine:
        mock_instance = MockEngine.return_value
        mock_instance.generate_rebuttal.return_value = "This is a mocked rebuttal."
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
    assert response.json()["llm_ready"] is True

def test_rebuttal_generation():
    payload = {
        "claim": "Vaccines contain microchips.",
        "fallacy_type": "False Cause",
        "fact_check_result": {
            "verdict": "false",
            "evidence": "Medical science confirms no microchips exist in vaccines.",
            "confidence": 0.99
        },
        "emotion": "angry",
        "tone": "casual"
    }
    response = client.post("/rebuttal", json=payload)
    assert response.status_code == 200
    assert response.json()["rebuttal"] == "This is a mocked rebuttal."

def test_rebuttal_empty_claim():
    payload = {
        "claim": "  ",
        "fallacy_type": "Ad Hominem",
        "fact_check_result": {"verdict": "unverified", "evidence": "", "confidence": 0.0},
        "emotion": "neutral",
        "tone": "formal"
    }
    response = client.post("/rebuttal", json=payload)
    assert response.status_code == 400
