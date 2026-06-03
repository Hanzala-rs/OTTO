# OTTO — Setup Guide

This guide walks you through setting up OTTO from scratch on a new machine.

---

## Prerequisites

- Docker Desktop (with Compose v2)
- Git
- Python 3.11+ (for running the ingestor from host)
- 8 GB RAM minimum (models load into memory)

---

## Step 1: Clone the Repository

```bash
git clone <repo-url>
cd OTTO
```

---

## Step 2: Configure Environment Variables

Copy the example env file and fill in your keys:

```bash
cp .env.example .env
```

Open `.env` and set the following required values:

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free Groq API key at: https://console.groq.com

---

## Step 3: Build and Start All Services

```bash
docker-compose up --build -d
```

This starts: PostgreSQL, Redpanda, Debezium, Qdrant, Redis, Backend, Frontend, Ingestion worker.

First build takes 10-20 minutes (downloads HuggingFace models into Docker volume).

Verify all services are running:

```bash
docker-compose ps
```

All containers should show status `Up` or `Up (healthy)`.

---

## Step 4: Register the Debezium CDC Connector

This is a one-time setup. Run it after `docker-compose up`.

On Windows (PowerShell):

```powershell
$body = @'
{
  "name": "otto-postgres-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.user": "otto_user",
    "database.password": "changeme0",
    "database.dbname": "otto",
    "database.server.name": "otto",
    "plugin.name": "pgoutput",
    "table.include.list": "public.documents",
    "topic.prefix": "otto",
    "key.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "key.converter.schemas.enable": "false",
    "value.converter.schemas.enable": "false",
    "topic.creation.enable": "true",
    "topic.creation.default.replication.factor": "1",
    "topic.creation.default.partitions": "3",
    "producer.override.max.request.size": "10485760",
    "max.queue.size": "20971520",
    "max.batch.size": "10485760",
    "snapshot.mode": "always"
  }
}
'@
Invoke-RestMethod -Uri "http://localhost:8083/connectors" -Method POST -ContentType "application/json" -Body $body
```

Verify it is running:

```powershell
Invoke-RestMethod "http://localhost:8083/connectors/otto-postgres-connector/status"
```

Both `connector.state` and `tasks[0].state` should be `RUNNING`.

---

## Step 5: Ingest Documents

Place your source files (`.md`, `.pdf`, `.docx`, `.txt`) inside the `datasets/` folder, then run:

```bash
docker-compose exec ingestion python file_ingestor.py
```

Monitor ingestion progress:

```bash
docker-compose logs -f ingestion
```

You should see lines like:

```
Ingested doc_id=1 lang=en chunks=12 op=r
```

---

## Step 6: Verify Data in Qdrant

Check that vectors have been stored:

Browser: Open `http://localhost:8333/dashboard`

PowerShell:

```powershell
Invoke-RestMethod "http://localhost:8333/collections/documents" | Select-Object -ExpandProperty result | Select-Object points_count
```

---

## Step 7: Open the App

Navigate to `http://localhost:3000` in your browser.

The chat widget is in the bottom-right corner. Type a question in English or Urdu, or record a voice note.

---

## Re-ingesting Data

If you change documents or need a fresh ingest:

```powershell
# 1. Wipe Qdrant
Invoke-RestMethod -Uri "http://localhost:8333/collections/documents" -Method DELETE

# 2. Truncate PostgreSQL
docker exec otto-postgres-1 psql -U otto_user -d otto -c "TRUNCATE TABLE documents RESTART IDENTITY CASCADE;"

# 3. Drop replication slot
docker exec otto-postgres-1 psql -U otto_user -d otto -c "SELECT pg_drop_replication_slot(slot_name) FROM pg_replication_slots;"

# 4. Delete connector, then re-register (Step 4)
Invoke-RestMethod -Uri "http://localhost:8083/connectors/otto-postgres-connector" -Method DELETE

# 5. Re-ingest
docker-compose exec ingestion python file_ingestor.py
```

---

## Stopping and Restarting

Stop all services (data is preserved in Docker volumes):

```bash
docker-compose down
```

Restart:

```bash
docker-compose up -d
```

After restart, re-register the Debezium connector (Step 4) if it is not running.

---

## Common Issues

**Backend shows "Failed to fetch" on first message**

The reranker model loads lazily on the first request. Wait 10-15 seconds and try again.

**Groq rate limit error (429)**

The free Groq tier allows 100,000 tokens per day. Wait for the daily limit to reset (resets at midnight UTC). Create a new Groq account for a fresh limit or upgrade to Dev Tier.

**Ingestion worker stuck on "Loading embedding model"**

Check for HuggingFace cache lock files:

```bash
docker exec otto-ingestion-1 sh -c "find /root/.cache/huggingface -name '*.lock' -delete"
docker-compose restart ingestion
```

**Debezium connector fails with RecordTooLargeException**

Set Redpanda message size limit:

```bash
docker exec otto-redpanda-1 rpk cluster config set kafka_batch_max_bytes 104857600
```

Then restart the connector task via the Debezium REST API.

---

## Environment Variables Reference

| Variable | Description | Default |
|---|---|---|
| POSTGRES_URL | PostgreSQL connection string | postgresql://otto_user:changeme0@postgres:5432/otto |
| POSTGRES_USER | DB username | otto_user |
| POSTGRES_PASSWORD | DB password | changeme0 |
| POSTGRES_DB | DB name | otto |
| QDRANT_URL | Qdrant endpoint | http://qdrant:8333 |
| QDRANT_COLLECTION | Collection name | documents |
| REDIS_URL | Redis connection | redis://redis:6379 |
| GROQ_API_KEY | Groq API key (required) | - |
| LLM_MODEL | Groq model ID | llama-3.3-70b-versatile |
| EMBEDDING_MODEL | HuggingFace embedding model | paraphrase-multilingual-MiniLM-L12-v2 |
| RERANKER_MODEL | HuggingFace cross-encoder | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| WHISPER_MODEL | Whisper model size | small |
| REDPANDA_BROKERS | Kafka broker | redpanda:9092 |
| REDPANDA_TOPIC_RAW | CDC topic name | otto.public.documents |
| SESSION_TTL_SECONDS | Chat session timeout | 1800 |
| CORS_ORIGINS | Allowed frontend origins | http://localhost:3000 |
