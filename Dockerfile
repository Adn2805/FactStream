FROM python:3.10-slim

# Install system dependencies for audio processing and networking
RUN apt-get update && apt-get install -y ffmpeg curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy all requirements files first to cache dependencies
COPY requirements.txt .
COPY frontend/requirements.txt frontend/
COPY services/gateway/requirements.txt services/gateway/
COPY services/nlu_service/requirements.txt services/nlu_service/
COPY services/vision_service/requirements.txt services/vision_service/
COPY services/factcheck_service/requirements.txt services/factcheck_service/
COPY services/genai_service/requirements.txt services/genai_service/
COPY services/scoring_service/requirements.txt services/scoring_service/

# Install global requirements
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install specific service requirements
RUN pip install --no-cache-dir -r frontend/requirements.txt && \
    pip install --no-cache-dir -r services/gateway/requirements.txt && \
    pip install --no-cache-dir "setuptools<70.0.0" wheel && \
    pip install --no-cache-dir -r services/nlu_service/requirements.txt && \
    pip install --no-cache-dir openai-whisper yt-dlp && \
    pip install --no-cache-dir -r services/vision_service/requirements.txt && \
    pip install --no-cache-dir -r services/factcheck_service/requirements.txt && \
    pip install --no-cache-dir -r services/genai_service/requirements.txt && \
    pip install --no-cache-dir -r services/scoring_service/requirements.txt

# Create models directories
RUN mkdir -p /app/models /app/services/genai_service/models

# Copy all source code
COPY . .

# Make the orchestration script executable
RUN chmod +x start.sh

# Expose the port HuggingFace routes to
EXPOSE 8501

# Command to run all services
CMD ["./start.sh"]
