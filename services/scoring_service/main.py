from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from scorer import CredibilityScorer

app = FastAPI(title="VisualDebate Scoring Service")

scorer = CredibilityScorer()

class FrameData(BaseModel):
    timestamp: float
    fallacy_type: str = "No Fallacy"
    fallacy_confidence: float = 0.0
    fact_check_verdict: str = "unverified"
    fact_check_confidence: float = 0.0
    emotion: str = "neutral"
    gaze: str = "at_camera"
    gesture_intensity: str = "low"

class ScoringRequest(BaseModel):
    frames: List[FrameData]

class AnomalyData(BaseModel):
    timestamp: float
    score: float

class ScoringResponse(BaseModel):
    credibility_score: float
    trend: str
    anomalies: List[AnomalyData]
    chart_base64: str

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/score", response_model=ScoringResponse)
async def calculate_score(request: ScoringRequest):
    if not request.frames:
        raise HTTPException(status_code=400, detail="Frames list cannot be empty")
        
    try:
        # Convert pydantic models to dicts
        frames_dict = [f.dict() for f in request.frames]
        result = scorer.analyze_timeline(frames_dict)
        return ScoringResponse(
            credibility_score=result["final_score"],
            trend=result["trend"],
            anomalies=[AnomalyData(**a) for a in result["anomalies"]],
            chart_base64=result["chart_base64"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
