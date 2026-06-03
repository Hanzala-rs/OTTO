import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from config.settings import get_settings
from api.routes import chat, voice, health

settings = get_settings()

# Enable LangSmith tracing if configured
if settings.langchain_tracing_v2 and settings.langchain_api_key:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("OTTO backend starting up...")
    # Warm up models on startup (avoids cold latency on first request)
    from rag.retriever import get_retriever
    from voice.stt import get_stt
    get_retriever()
    get_stt()
    logger.info("Models loaded. Ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="OTTO — Multilingual RAG API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(voice.router, prefix="/voice", tags=["voice"])
