  # Fix Report — 2026-10-26

## Bugs fixed
| # | Symptom | Root cause | Fix |
|---|---------|-----------|-----|
| 1 | `/voice` 500: Qdrant `timed out` | Keyword fallback scrolled the **whole** collection per query | One filtered scroll (`MatchText`, limit 50) + full-text index on `text` — `rag/retriever.py`, `ingestion/workers/qdrant_upserter.py` |
| 2 | `/chat` 500: Qdrant `timed out` in `fetch_parent` | 5 sequential unindexed lookups, stalled by Docker VM swapping | Keyword index on `chunk_id` + single batched `fetch_parents()` (`MatchAny`) — `rag/retriever.py`, `rag/pipeline.py` |
| 3 | Whole API froze during a voice request | Sync `graph.invoke`/STT/ffmpeg inside `async def` | `run_in_threadpool` — `api/routes/chat.py`, `api/routes/voice.py` |
| 4 | Hangs instead of errors | No client timeouts | Qdrant `timeout=10` (`QDRANT_TIMEOUT`), Redis 2 s, LLM 20 s |
| 5 | `VAD check failed` every request | `torchaudio` can't decode webm from BytesIO | Decode once via ffmpeg to 16 kHz numpy, shared by VAD + Whisper — `voice/audio_formatter.py`, `vad.py`, `stt.py` |
| 6 | Slow first request | VAD + reranker lazy-loaded | Warmed at startup — `main.py` |
| 7 | Qdrant unreachable from host | Port map `8333:6333`, Qdrant listens on 8333 | `8333:8333` — `docker-compose.yml` |
| 8 | No LLM proxy; HyDE `Connection error` | Direct Groq calls, no retry/fallback | LiteLLM service (`infra/litellm/config.yaml`): retries 2, timeout 20 s, fallback → `llama-3.1-8b-instant`; backend uses `ChatOpenAI` → `http://litellm:4000` |
| 9 | Voice 85 s | Whisper `medium` under swap, beam 5, extra HyDE LLM call | `WHISPER_MODEL=small`, greedy decode, HyDE skipped for voice |
| 10 | Re-ingest would break search | `VECTOR_DIM` default 1024 vs 384-dim MiniLM | Reverted to 384 |

## Tests run (all on rebuilt stack)
| Test | Result |
|------|--------|
| `curl localhost:8333/collections` | ✅ 200 |
| LiteLLM `/v1/chat/completions` model `otto-llm` | ✅ 200, 7.0 s |
| Groq reachability from container | ✅ 401 w/o key (network OK) |
| `/chat` normal + weak-match query | ✅ 200 / 200 (8.9 s, 7.6 s), no timeouts |
| `/health` during in-flight `/voice` | ✅ 200 in 26 ms (event loop free) |
| `/voice` webm clip, transcript correct, no VAD warning | ✅ 200 |

## Voice latency (`voice_logs`, ms)
| Run | STT | RAG | TTS | Total |
|-----|-----|-----|-----|-------|
| Before | 19 039 | 11 177 | 2 469 | ~85 s observed in browser |
| After Phase 1+2 | 25 960 | 11 671 | 5 596 | 43 621 |
| After Phase 3 (warm) | 6 007 | 7 311 | 2 228 | **15 667** |

## Voice → `otto-llm-fast`
- `llama-3.1-8b-instant` returns **404** on this Groq account. `otto-llm-fast` now points to `groq/openai/gpt-oss-20b` with `reasoning_effort: low`.
- Voice now uses `LLM_VOICE_MODEL` (default `otto-llm-fast`); chat keeps `otto-llm`. Changed: `rag/llm_client.py`, `rag/pipeline.py`, `config/settings.py`.
- Test: 3 × `/voice` → 200, valid answers, totals 13.4 / 22.0 / 22.4 s.
- LLM alone through LiteLLM: 120b 0.82–0.86 s, 20b 0.61–0.77 s. **The LLM isn't the bottleneck.** The remaining RAG time (6–12 s) is local CPU work (embedding and rerank) under swap.

- The 404 errors at 11:12 in the logs came from the old `llama-3.1-8b-instant` config, before the switch to `gpt-oss-20b`. Added a reverse fallback `otto-llm-fast` → `otto-llm`. LiteLLM `/router/settings` confirms both fallbacks are loaded. A normal fast-model call returns 200.

## Timeout recurrence (11:37)
- `voice_logs` showed STT at **83.9 s** for a 3 s Urdu clip; RAG 10 s and TTS 4 s were normal.
- Cause: the Docker VM was capped at 5.7 GB (the WSL default, 50% of 11.8 GB). After the full-stack restart, debezium, redpanda and ingestion pushed it into swap, leaving 126 MB free. Redpanda logged "Reactor stalled".
- An isolated test of the same kind of Urdu clip took 7–9 s of STT, so this is not a code bug.
- Fix: created `C:\Users\admin\.wslconfig` with `memory=8GB, swap=4GB`. It needs `wsl --shutdown` and a Docker Desktop restart to take effect.

- **Retest after the 8 GB change:** Docker MemTotal 8.3 GB, swap use 1 MB. 6 × `/voice` (3 en, 3 ur) all returned 200 in 15.9–24.1 s, under the 60 s abort. STT took 6–10 s, RAG 5–14 s and TTS 1–3 s. No errors in the backend log.

## Urdu answers
| Symptom | Root cause | Fix |
|---|---|---|
| Urdu questions get "I don't have details" while the same question in English is answered | Corpus, keyword fallback and reranker (`ms-marco-MiniLM`) are English-only, so Urdu queries retrieve and rerank badly | `to_search_query()` translates Urdu-script queries to English with `otto-llm-fast` (~1 s); that query drives retrieval, HyDE and rerank, and the answer stays in Urdu. Changed: `rag/query_engine.py`, `rag/pipeline.py` (`search_query` state), `config/prompts.py` (`TRANSLATE_PROMPT`) |
| Refusal is in English for Urdu users | Prompt hardcoded the English sentence | Prompt now asks for the refusal in the user's language, with the Urdu sentence given |

**Tests** (run inside the container; Windows git-bash curl garbles Urdu request bodies, which gave false failures):
- Chat (ur) "chairman": 7.3 s, Urdu answer "Abbas D. Habib". ✅
- Chat (ur) off-topic: Urdu refusal. ✅ Chat (en) off-topic: English refusal. ✅
- Voice (ur) ×3: 200 in 14.5–16.4 s. Two runs answered and one refused in Urdu.

**Data gap:** the corpus never states the *first* chairman of Bank AL Habib; it only names "Founder Member & Chairman" and "first Chairman of Habib Bank", a different bank. Answers to that question vary between runs; adding the fact to the KB is the real fix.

## Voice: formatted text plus clean speech
- **Before:** TTS read markdown symbols aloud (`**`, `|`, `#`).
- **Fix:** `_speech_text()` in `voice/tts.py` strips markdown only for TTS. Table rows become "a, b." and heading, bullet and bold marks are removed. The `X-Response` text shown in the UI keeps its markdown.
- **Tests:**
  - Unit check on a table, bullet and Urdu-heading sample: clean output. ✅
  - Voice (en): 200, 32.3 s. ✅
  - Voice (ur): 200, 21.4 s. ✅

- **Spoken table cap:** speech reads at most 3 table rows (`MAX_SPOKEN_ROWS` in `voice/tts.py`), drops the header row, and adds "More details are shown on screen." in English or Urdu. The full table stays in the `X-Response` text.
- **Tests:**
  - Unit check: a 5-row table is spoken as 3 rows plus the hint (en and ur); a 2-row table is spoken in full with no hint. ✅
  - Voice: en 14.4 s and 16.5 s, ur 16.7 s, all 200. Client times match the server's `total_latency_ms`. ✅

## Open issues
- Docker VM has 5.7 GB RAM and is ~1.5 GB into swap; this inflates every stage. Raise Docker Desktop memory to 8 GB+ or stop unused services (debezium/redpanda/adminer) in dev.
- RAG ~7 s is mostly `openai/gpt-oss-120b` reasoning. Switching voice to `otto-llm-fast` would cut it further (needs quality check).
- `LLM_MODEL` in `.env` no longer selects the model; edit `infra/litellm/config.yaml` instead.
- Frontend voice abort is still 60 s (`frontend/lib/api.ts:44`); lower after p95 confirmed.
