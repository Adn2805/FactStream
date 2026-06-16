FROM python:3.10-slim

WORKDIR /app

# llama-cpp-python requires a C++ compiler to build the wheel
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install llama-cpp-python (this builds the C++ backend for CPU by default)
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8004

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
