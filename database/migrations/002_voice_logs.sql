-- Voice session logs for monitoring latency, language distribution, TTS engine usage
CREATE TABLE IF NOT EXISTS voice_logs (
    id              SERIAL PRIMARY KEY,
    session_id      TEXT NOT NULL,
    transcript      TEXT,
    detected_lang   CHAR(2),
    tts_engine      TEXT,   -- 'elevenlabs' | 'coqui'
    stt_latency_ms  INT,
    tts_latency_ms  INT,
    rag_latency_ms  INT,
    total_latency_ms INT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_voice_logs_session ON voice_logs (session_id);
CREATE INDEX idx_voice_logs_lang ON voice_logs (detected_lang);
CREATE INDEX idx_voice_logs_created ON voice_logs (created_at DESC);
