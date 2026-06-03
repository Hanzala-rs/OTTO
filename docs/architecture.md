# OTTO — System Architecture

OTTO is a multilingual RAG (Retrieval-Augmented Generation) assistant for Bank AL Habib. It supports English, Urdu (Nastaliq script), and Roman Urdu, with both text and voice interfaces.

---

## High-Level Architecture

```
User (Browser)
    |
    | HTTP
    v
Frontend (Next.js :3000)
    |
    | REST API
    v
Backend (FastAPI :8000)
    |
    +-- Text query --> LangGraph RAG Pipeline --> Groq LLM --> Response
    |
    +-- Voice query --> Whisper STT --> RAG Pipeline --> edge-tts --> Audio

RAG Pipeline:
    Guardrails --> HyDE --> Qdrant Retriever --> Reranker --> LLM

Data Pipeline:
    Documents (files) --> file_ingestor.py --> PostgreSQL
        --> Debezium CDC --> Redpanda (Kafka)
        --> Ingestion Worker --> Chunk + Embed --> Qdrant
```

---

## Services

| Service | Image / Stack | Port | Purpose |
|---|---|---|---|
| frontend | Next.js 14, TypeScript, Tailwind | 3000 | Chat UI |
| backend | FastAPI, LangGraph, Python 3.11 | 8000 | RAG API |
| postgres | postgres:16 | 5432 | Document storage + CDC source |
| redpanda | redpandadata/redpanda | 9092 | Kafka-compatible message broker |
| debezium | debezium/connect:2.5 | 8083 | CDC connector (Postgres to Redpanda) |
| qdrant | qdrant/qdrant | 8333 | Vector database |
| redis | redis:7-alpine | 6379 | Session/conversation history cache |
| ingestion | Python worker | - | Consumes CDC events, embeds, upserts |

---

## Data Ingestion Pipeline

```
1. Place files in datasets/
2. Run file_ingestor.py
      Reads: .pdf, .docx, .doc, .txt, .md
      Inserts rows into: PostgreSQL public.documents

3. Debezium (CDC) detects INSERT events on public.documents
      Streams events to Redpanda topic: otto.public.documents

4. Ingestion worker (workers/consumer.py) consumes messages
      - Detects language (langdetect)
      - Chunks text (ParentChildChunker)
      - Embeds chunks (paraphrase-multilingual-MiniLM-L12-v2, 384 dim)
      - Upserts to Qdrant collection: documents
```

### Chunking Strategy

Parent-child chunking is used:
- Parent chunks: larger context windows (fed to LLM)
- Child chunks: smaller, precise units (used for vector search)

When a child chunk matches a query, its parent is fetched for the full context.

---

## RAG Query Pipeline (LangGraph)

```
User query
    |
    v
[guardrails_node]    -- rejects empty, too-long, injection attempts
    |
    v
[hyde_node]          -- generates a hypothetical answer to improve retrieval
    |
    v
[retriever_node]     -- dense vector search in Qdrant (top 20 results)
    |
    v
[reranker_node]      -- cross-encoder reranks top 20 to top 5, fetches parent text
    |
    v
[llm_node]           -- Groq LLM (llama-3.3-70b-versatile) with context + history
    |
    v
Response
```

---

## Voice Pipeline

```
User records audio (WebRTC via browser)
    |
    v
Frontend sends audio blob to POST /voice
    |
    v
[VAD check]          -- voice activity detection, skips silent audio
    |
    v
[Whisper STT]        -- faster-whisper (small model, CPU, int8)
      detects language: "en" or "ur"
    |
    v
[RAG Pipeline]       -- same as text query using transcript
    |
    v
[TTS]                -- edge-tts
      English: en-US-GuyNeural (male)
      Urdu:    ur-PK-AsadNeural (male)
    |
    v
MP3 audio returned to frontend
```

---

## Models

| Model | Used For | Size | Provider |
|---|---|---|---|
| paraphrase-multilingual-MiniLM-L12-v2 | Embeddings (ingestion + retrieval) | ~118 MB | HuggingFace |
| cross-encoder/ms-marco-MiniLM-L-6-v2 | Reranking | ~22 MB | HuggingFace |
| faster-whisper small | Speech-to-text | ~242 MB | HuggingFace |
| llama-3.3-70b-versatile | LLM responses | API | Groq |
| edge-tts | Text-to-speech | API | Microsoft |

---

## Key Configuration (.env)

```
POSTGRES_URL        -- PostgreSQL connection string
QDRANT_URL          -- Qdrant REST endpoint
REDIS_URL           -- Redis connection string
GROQ_API_KEY        -- Groq API key (LLM)
EMBEDDING_MODEL     -- HuggingFace embedding model name
RERANKER_MODEL      -- HuggingFace cross-encoder model name
WHISPER_MODEL       -- Whisper model size (tiny/small/medium)
REDPANDA_BROKERS    -- Kafka broker address
REDPANDA_TOPIC_RAW  -- Topic name for CDC events (otto.public.documents)
LLM_MODEL           -- Groq model ID
```

---

## Directory Structure

```
OTTO/
├── backend/                  FastAPI backend
│   ├── api/routes/           chat.py, voice.py endpoints
│   ├── config/               settings.py, prompts.py
│   ├── memory/               Redis session history
│   ├── rag/                  pipeline.py, retriever.py, reranker.py, llm_client.py
│   └── voice/                stt.py, tts.py, vad.py
├── frontend/                 Next.js frontend
│   ├── app/                  Next.js app router (layout, page, globals.css)
│   ├── components/widget/    ChatWidget, ChatWindow, MessageBubble, AudioPlayer, VoiceInput
│   └── hooks/                useChat.ts, useVoiceRecorder.ts, useAudioPlayer.ts
├── ingestion/                Data pipeline
│   ├── workers/              consumer.py, chunker.py, embedder.py, qdrant_upserter.py
│   ├── readers/              pdf_reader.py, docx_reader.py, text_reader.py
│   ├── schemas/              document_schema.py
│   ├── debezium/             connector-config.json, register-connector.sh
│   ├── file_ingestor.py      Seeds documents into PostgreSQL
│   └── direct_ingest.py      Bypasses CDC, ingests directly to Qdrant
├── datasets/                 Source documents (.md, .pdf, .docx, .txt)
├── database/migrations/      PostgreSQL schema
├── docker-compose.yml        Local development stack
├── docker-compose.prod.yml   Production stack
└── docs/                     This documentation
```
