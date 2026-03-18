# Whatsapp Companion — Project Planning

## Changes Log

### 2026-03-17 — Env centralization + model fixes

**Env centralization**
- Moved shared API keys (Groq, ElevenLabs, Together, Qdrant) to `~/.env/.env`
- Local `.env` kept for project-specific vars: `WHATSAPP_*`, `NGROK_URL`, `LANGSMITH_PROJECT`
- `docker-compose.yml`: both `chainlit` and `whatsapp` services load `~/.env/.env` then `.env`
- `settings.py`: loads `(~/.env/.env, .env)` via `pydantic-settings` for local runs

**Decommissioned model fixes**
- `SMALL_TEXT_MODEL_NAME`: `gemma2-9b-it` → `llama-3.1-8b-instant` (Groq decommissioned gemma2)
- `TTI_MODEL_NAME`: `FLUX.1-schnell-Free` → `FLUX.1-schnell` (Together removed free serverless endpoint)

**LangSmith**
- Tracing enabled; project: `whatsapp_companion-456`
