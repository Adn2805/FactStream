import os
import torch
import subprocess
import whisper
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import BertTokenizer, BertForSequenceClassification
import torch.nn.functional as F
from dataset import FALLACY_CLASSES, ID_TO_FALLACY

app = FastAPI(title="VisualDebate NLU Service", description="Detects logical fallacies using BERT and extracts audio transcripts using Whisper", version="1.0.0")

MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models", "fallacy_bert"))

# Global variables for models
model = None
tokenizer = None
whisper_model = None
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class AnalyzeRequest(BaseModel):
    text: str

class AnalyzeResponse(BaseModel):
    fallacy: str
    confidence: float
    explanation: str

class TranscribeRequest(BaseModel):
    video_url: str

class TranscribeResponse(BaseModel):
    transcript: str

@app.on_event("startup")
async def load_model():
    global model, tokenizer, whisper_model
    try:
        if os.path.exists(MODEL_PATH) and os.listdir(MODEL_PATH):
            print(f"Loading custom fine-tuned model from {MODEL_PATH}")
            tokenizer = BertTokenizer.from_pretrained(MODEL_PATH)
            model = BertForSequenceClassification.from_pretrained(MODEL_PATH)
        else:
            print("Custom model not found. Loading base bert for placeholder execution. RUN train.py FIRST!")
            tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
            model = BertForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=len(FALLACY_CLASSES))
            
        model.to(device)
        model.eval()
    except Exception as e:
        print(f"Failed to load NLU model: {e}")

    try:
        print("Loading Whisper base model for transcription...")
        whisper_model = whisper.load_model("base", device="cpu")
    except Exception as e:
        print(f"Failed to load Whisper model: {e}")

@app.get("/health")
async def health_check():
    return {"status": "ok", "device": str(device), "nlu_loaded": model is not None, "whisper_loaded": whisper_model is not None}

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model is currently unavailable.")

    try:
        inputs = tokenizer(request.text, return_tensors="pt", truncation=True, padding=True, max_length=128).to(device)
        
        with torch.no_grad():
            outputs = model(**inputs)
            
        logits = outputs.logits
        probs = F.softmax(logits, dim=1)
        
        confidence, predicted_class_id = torch.max(probs, dim=1)
        confidence = confidence.item()
        predicted_class_id = predicted_class_id.item()
        
        fallacy_name = ID_TO_FALLACY.get(predicted_class_id, "Unknown")
        
        explanation = f"The statement exhibits characteristics commonly associated with {fallacy_name}."
        if fallacy_name == "No Fallacy":
            explanation = "The statement appears to be logically sound without clear fallacies."
            
        return AnalyzeResponse(
            fallacy=fallacy_name,
            confidence=round(confidence, 4),
            explanation=explanation
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(request: TranscribeRequest):
    if not whisper_model:
        raise HTTPException(status_code=503, detail="Whisper model unavailable")
        
    url = request.video_url
    audio_path = f"temp_audio_{hash(url)}.wav"
    try:
        # Download audio using yt-dlp
        print(f"Downloading audio stream from {url}")
        subprocess.run(["yt-dlp", "-x", "--audio-format", "wav", "-o", audio_path, url], check=True, capture_output=True)
        
        # Transcribe with whisper
        print("Transcribing audio...")
        result = whisper_model.transcribe(audio_path, fp16=False)
        return TranscribeResponse(transcript=result["text"])
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"yt-dlp download failed: {e.stderr.decode()}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)
