# Use official python slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for NLTK and building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir "setuptools<70.0.0" wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir openai-whisper yt-dlp

# Download NLTK data for data augmentation
RUN python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"

# Copy application code
COPY . .

# Expose the port
EXPOSE 8001

# Run the FastAPI application using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
