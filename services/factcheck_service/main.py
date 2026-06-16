from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag_pipeline import RAGPipeline

app = FastAPI(title="VisualDebate Fact-Check Service")

pipeline = None

class FactCheckRequest(BaseModel):
    claim: str

class FactCheckResponse(BaseModel):
    verdict: str
    evidence: str
    confidence: float

@app.on_event("startup")
async def startup_event():
    global pipeline
    try:
        pipeline = RAGPipeline()
    except Exception as e:
        print(f"Failed to initialize RAG pipeline: {e}")

@app.get("/health")
async def health_check():
    return {"status": "ok", "pipeline_ready": pipeline is not None}

@app.post("/factcheck", response_model=FactCheckResponse)
async def factcheck_claim(request: FactCheckRequest):
    if not request.claim.strip():
        raise HTTPException(status_code=400, detail="Claim cannot be empty")
        
    if pipeline is None:
        raise HTTPException(status_code=503, detail="RAG Pipeline not ready")
        
    try:
        result = pipeline.factcheck(request.claim)
        return FactCheckResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
