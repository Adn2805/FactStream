from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llm_engine import LLMEngine
import asyncio

app = FastAPI(title="VisualDebate GenAI Service")

engine = None

class FactCheckData(BaseModel):
    verdict: str
    evidence: str
    confidence: float

class RebuttalRequest(BaseModel):
    claim: str
    fallacy_type: str
    fact_check_result: FactCheckData
    emotion: str
    tone: str = "formal"

class RebuttalResponse(BaseModel):
    rebuttal: str

@app.on_event("startup")
async def startup_event():
    global engine
    try:
        # Offload model loading to a separate thread to not block the event loop
        loop = asyncio.get_event_loop()
        engine = await loop.run_in_executor(None, LLMEngine)
    except Exception as e:
        print(f"Failed to load LLM Engine: {e}")

@app.get("/health")
async def health_check():
    return {"status": "ok", "llm_ready": engine is not None}

@app.post("/rebuttal", response_model=RebuttalResponse)
async def generate_rebuttal(request: RebuttalRequest):
    if engine is None:
        raise HTTPException(status_code=503, detail="LLM Engine is currently unavailable or downloading.")
        
    if not request.claim.strip():
        raise HTTPException(status_code=400, detail="Claim cannot be empty")
        
    try:
        rebuttal_text = engine.generate_rebuttal(
            claim=request.claim,
            fallacy=request.fallacy_type,
            fact_check=request.fact_check_result.dict(),
            emotion=request.emotion,
            tone=request.tone
        )
        return RebuttalResponse(rebuttal=rebuttal_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
