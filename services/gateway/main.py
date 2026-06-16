import os
import httpx
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

app = FastAPI(title="VisualDebate API Gateway")

# Service URLs from env or defaults
NLU_URL = os.getenv("NLU_SERVICE_URL", "http://nlu_service:8001")
VISION_URL = os.getenv("VISION_SERVICE_URL", "http://vision_service:8002")
FACTCHECK_URL = os.getenv("FACTCHECK_SERVICE_URL", "http://factcheck_service:8003")
GENAI_URL = os.getenv("GENAI_SERVICE_URL", "http://genai_service:8004")
SCORING_URL = os.getenv("SCORING_SERVICE_URL", "http://scoring_service:8005")

class AnalysisResponse(BaseModel):
    nlu_fallacy: str
    fact_check_verdict: str
    rebuttal: str
    scoring_data: dict

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "gateway"}

import re
from youtube_transcript_api import YouTubeTranscriptApi

def extract_video_id(url: str) -> str:
    """Extract YouTube Video ID from URL."""
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_pipeline(
    transcript: str = Form(""),
    video_url: str = Form(""),
    video: UploadFile = File(None)
):
    """
    Orchestrates the full ML pipeline asynchronously via httpx.
    """
    # 0. Handle Video URL Auto-Transcription
    if video_url and not transcript.strip():
        video_id = extract_video_id(video_url)
        if video_id:
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                transcript = " ".join([t['text'] for t in transcript_list])
            except Exception:
                pass # Proceed to whisper fallback
        
        # Fallback to Whisper Transcription on NLU Service
        if not transcript.strip():
            async with httpx.AsyncClient(timeout=300.0) as client:
                try:
                    transcribe_res = await client.post(f"{NLU_URL}/transcribe", json={"video_url": video_url})
                    transcribe_res.raise_for_status()
                    transcript = transcribe_res.json().get("transcript", "Failed to get transcript string.")
                except Exception as e:
                    transcript = f"Failed to transcribe video using Whisper fallback: {e}"

    async with httpx.AsyncClient(timeout=300.0) as client:
        # 1. Vision Service (Mocked since we didn't implement the YOLOv8 code in previous phases)
        vision_data = {"emotion": "confident", "gaze": "at_camera", "gesture_intensity": "low"}
        
        # 2. NLU Service
        try:
            nlu_res = await client.post(f"{NLU_URL}/analyze", json={"text": transcript})
            nlu_res.raise_for_status()
            nlu_data = nlu_res.json()
        except Exception as e:
            nlu_data = {"fallacy": "No Fallacy", "confidence": 0.0, "explanation": str(e)}

        # 3. Fact-Check Service
        try:
            fc_res = await client.post(f"{FACTCHECK_URL}/factcheck", json={"claim": transcript})
            fc_res.raise_for_status()
            fc_data = fc_res.json()
        except Exception as e:
            fc_data = {"verdict": "unverified", "evidence": "", "confidence": 0.0}

        # 4. GenAI Service
        try:
            gen_payload = {
                "claim": transcript,
                "fallacy_type": nlu_data.get("fallacy", "No Fallacy"),
                "fact_check_result": fc_data,
                "emotion": vision_data.get("emotion", "neutral"),
                "tone": "formal"
            }
            gen_res = await client.post(f"{GENAI_URL}/rebuttal", json=gen_payload)
            gen_res.raise_for_status()
            gen_data = gen_res.json()
        except Exception as e:
            gen_data = {"rebuttal": f"Could not generate rebuttal: {e}"}

        # 5. Scoring Service (We simulate a batch of frames based on this single request for the demo)
        try:
            frame = {
                "timestamp": 0.0,
                "fallacy_type": nlu_data.get("fallacy", "No Fallacy"),
                "fallacy_confidence": nlu_data.get("confidence", 0.0),
                "fact_check_verdict": fc_data.get("verdict", "unverified"),
                "fact_check_confidence": fc_data.get("confidence", 0.0),
                "emotion": vision_data.get("emotion"),
                "gaze": vision_data.get("gaze"),
                "gesture_intensity": vision_data.get("gesture_intensity")
            }
            import random
            frames_batch = []
            for i in range(20):
                sim_frame = frame.copy()
                sim_frame["timestamp"] = float(i)
                sim_frame["fallacy_confidence"] = max(0.0, min(1.0, frame.get("fallacy_confidence", 0.0) + random.uniform(-0.15, 0.15)))
                sim_frame["fact_check_confidence"] = max(0.0, min(1.0, frame.get("fact_check_confidence", 0.0) + random.uniform(-0.1, 0.1)))
                frames_batch.append(sim_frame)
            
            score_res = await client.post(f"{SCORING_URL}/score", json={"frames": frames_batch})
            score_res.raise_for_status()
            score_data = score_res.json()
        except Exception as e:
            score_data = {"credibility_score": 50.0, "trend": "stable", "anomalies": [], "chart_base64": ""}

    return AnalysisResponse(
        nlu_fallacy=nlu_data.get("fallacy", "No Fallacy"),
        fact_check_verdict=fc_data.get("verdict", "unverified"),
        rebuttal=gen_data.get("rebuttal", ""),
        scoring_data=score_data
    )
