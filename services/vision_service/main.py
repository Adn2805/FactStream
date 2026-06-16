from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="VisualDebate Mock Vision Service")

class VisionResponse(BaseModel):
    emotion: str
    gaze: str
    gesture_intensity: str

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/analyze", response_model=VisionResponse)
async def analyze_frame():
    # Mocking vision response for the demo since YOLO/OpenCV were not fully implemented
    return VisionResponse(
        emotion="confident",
        gaze="at_camera",
        gesture_intensity="low"
    )
