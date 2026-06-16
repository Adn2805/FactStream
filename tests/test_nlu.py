import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Add the nlu_service to sys.path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'services', 'nlu_service')))

from main import app, load_model

client = TestClient(app)

# We need to manually call startup events in TestClient
@pytest.fixture(autouse=True)
def run_startup():
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(load_model())

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "device" in data
    assert "model_loaded" in data

def test_analyze_empty_text():
    response = client.post("/analyze", json={"text": "   "})
    assert response.status_code == 400
    assert "Text cannot be empty" in response.json()["detail"]

def test_analyze_valid_text():
    # Since the model might just be the randomly initialized fallback,
    # we just test that the endpoint returns the correct schema
    response = client.post("/analyze", json={"text": "You are stupid, therefore your argument is wrong."})
    assert response.status_code == 200
    data = response.json()
    assert "fallacy" in data
    assert "confidence" in data
    assert "explanation" in data
    assert isinstance(data["confidence"], float)

@patch('main.model')
def test_analyze_model_unavailable(mock_model):
    # Simulate model being None
    import main
    main.model = None
    response = client.post("/analyze", json={"text": "Testing unavailable model"})
    assert response.status_code == 503
    assert "Model is currently unavailable" in response.json()["detail"]
