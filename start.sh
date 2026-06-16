#!/bin/bash

# Define internal localhost URLs for the Gateway to communicate with
export NLU_URL="http://localhost:8001"
export VISION_URL="http://localhost:8002"
export FACTCHECK_URL="http://localhost:8003"
export GENAI_URL="http://localhost:8004"
export SCORING_URL="http://localhost:8005"
export GATEWAY_URL="http://localhost:8000"

echo "Starting NLU Service on port 8001..."
cd /app/services/nlu_service
uvicorn main:app --host 0.0.0.0 --port 8001 &

echo "Starting Vision Service (Mock) on port 8002..."
cd /app/services/vision_service
uvicorn main:app --host 0.0.0.0 --port 8002 &

echo "Starting FactCheck Service on port 8003..."
cd /app/services/factcheck_service
uvicorn main:app --host 0.0.0.0 --port 8003 &

echo "Starting GenAI Service on port 8004..."
cd /app/services/genai_service
uvicorn main:app --host 0.0.0.0 --port 8004 &

echo "Starting Scoring Service on port 8005..."
cd /app/services/scoring_service
uvicorn main:app --host 0.0.0.0 --port 8005 &

echo "Starting API Gateway on port 8000..."
cd /app/services/gateway
uvicorn main:app --host 0.0.0.0 --port 8000 &

echo "Starting Frontend on port 8501..."
cd /app/frontend
# HuggingFace Spaces routes external traffic to port 8501 automatically
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
