# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Build and run
make ava-build        # Build Docker containers
make ava-run          # Run containers (background)
make ava-stop         # Stop containers
make ava-delete       # Delete containers and memory databases

# Code quality (uses Ruff, line-length: 120)
make format-fix       # Fix formatting and imports
make lint-fix         # Fix linting issues
make format-check     # Check formatting without fixing
make lint-check       # Check linting without fixing
```

No test suite is configured in this project.

## Architecture

This is **Ava**, a WhatsApp AI companion built on **LangGraph**. The core is a directed graph that processes messages through a pipeline of nodes.

### Graph Workflow (`src/ai_companion/graph/`)

Eight nodes executed in order:

1. `memory_extraction_node` — Extracts facts from messages for long-term storage
2. `router_node` — Classifies response type: `conversation | image | audio`
3. `context_injection_node` — Injects schedule-based activity context
4. `memory_injection_node` — Retrieves semantically similar memories from Qdrant
5. `conversation_node` / `image_node` / `audio_node` — Generates the response (conditional)
6. `summarize_conversation_node` — Compresses history when messages exceed threshold

Routing logic lives in `edges.py`. State shape is in `state.py` (`AICompanionState` extends LangChain's `MessagesState`).

### Interfaces

- **WhatsApp** (`interfaces/whatsapp/`) — FastAPI webhook that receives and sends text/image/audio via WhatsApp Cloud API
- **Chainlit** (`interfaces/chainlit/app.py`) — Web UI for local testing with streaming and multimodal playback

### Modules

Swappable AI capability modules in `src/ai_companion/modules/`:
- `speech/` — STT via Groq Whisper, TTS via ElevenLabs
- `image/` — Image generation via Together AI (FLUX), vision via Groq LLaVA
- `memory/long_term/` — Qdrant vector store + memory manager for cross-session recall

Module instances are cached as singletons via helpers in `graph/utils/helpers.py`.

### Memory Architecture

Two-tier memory:
- **Short-term**: SQLite async checkpointer (LangGraph) — persists full conversation state per `thread_id`
- **Long-term**: Qdrant vector DB — stores extracted facts as embeddings, retrieved by semantic similarity

Key thresholds (configurable in `settings.py`):
- `TOTAL_MESSAGES_SUMMARY_TRIGGER`: 20 — triggers conversation summarization
- `TOTAL_MESSAGES_AFTER_SUMMARY`: 5 — messages retained after summarization
- `MEMORY_TOP_K`: 3 — memories retrieved per turn

### Key Files

| File | Purpose |
|------|---------|
| `src/ai_companion/graph/nodes.py` | All node implementations |
| `src/ai_companion/graph/graph.py` | Graph construction and compilation |
| `src/ai_companion/core/prompts.py` | All system prompts |
| `src/ai_companion/settings.py` | Pydantic settings (all env vars) |
| `docker-compose.yml` | Services: qdrant, chainlit, whatsapp |

### Environment Variables

Copy `.env.example` to `.env`. Required keys:
- `GROQ_API_KEY` — LLM (llama-3.3-70b-versatile) and STT (Whisper)
- `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID` — TTS
- `TOGETHER_API_KEY` — Image generation
- `QDRANT_URL` + `QDRANT_API_KEY` — Vector DB
- `WHATSAPP_PHONE_NUMBER_ID` + `WHATSAPP_TOKEN` + `WHATSAPP_VERIFY_TOKEN` — WhatsApp Cloud API
