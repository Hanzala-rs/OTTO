# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev curl git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel

# pip cache mount — packages never re-downloaded even if requirements.txt changes
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# HuggingFace model cache — model never re-downloaded after first build
RUN --mount=type=cache,target=/root/.cache/huggingface \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"

COPY . .

CMD ["python", "-m", "workers.consumer"]
