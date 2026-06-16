import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'services', 'scoring_service')))

from main import app
from scorer import CredibilityScorer

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200

def test_scorer_bounds():
    scorer = CredibilityScorer()
    
    # Perfect frame
    perfect_frame = {
        "fact_check_verdict": "true",
        "fact_check_confidence": 1.0,
        "emotion": "confident",
        "gaze": "at_camera"
    }
    score = scorer.compute_frame_score(perfect_frame)
    assert score <= 100.0
    
    # Terrible frame
    terrible_frame = {
        "fallacy_type": "Ad Hominem",
        "fallacy_confidence": 1.0,
        "fact_check_verdict": "false",
        "fact_check_confidence": 1.0,
        "emotion": "deceptive",
        "gesture_intensity": "high",
        "gaze": "away"
    }
    score = scorer.compute_frame_score(terrible_frame)
    assert score >= 0.0

def test_scoring_endpoint():
    payload = {
        "frames": [
            {"timestamp": 0.0, "emotion": "confident"},
            {"timestamp": 1.0, "emotion": "confident"},
            {"timestamp": 2.0, "emotion": "deceptive", "fact_check_verdict": "false", "fact_check_confidence": 0.9},
            {"timestamp": 3.0, "emotion": "angry", "fallacy_type": "Ad Hominem", "fallacy_confidence": 0.8}
        ]
    }
    response = client.post("/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "credibility_score" in data
    assert "trend" in data
    assert "anomalies" in data
    assert "chart_base64" in data
    
    # We expect a declining trend given the data
    assert data["trend"] == "declining"
    # We expect an anomaly due to the sharp drop
    assert len(data["anomalies"]) > 0

def test_empty_frames():
    payload = {"frames": []}
    response = client.post("/score", json=payload)
    assert response.status_code == 400
