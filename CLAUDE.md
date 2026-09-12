# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Python/FastAPI Instagram chatbot that auto-replies to DMs and post comments, adopting the persona of a natural-medicine/supplements specialist ("NaturBot"). It uses a dynamic LLM provider factory (OpenRouter, DeepSeek, or OpenAI-compatible APIs), persists chat history in local SQLite for contextual memory, and has a stubbed-out RAG layer for future Markdown knowledge-base search.

## Commands

```bash
# Setup
python -m venv .env && source .env/bin/activate
pip install -r requirements.txt
cp .env.template .env   # then fill in tokens/keys

# Run the server
uvicorn main:app --reload   # http://127.0.0.1:8000, docs at /docs

# Run tests
pytest -v
pytest tests/test_webhook_service.py -v   # single file
pytest tests/test_webhook_service.py::test_process_incoming_dm -v   # single test

# Local webhook tunnel (for real Meta integration testing)
ngrok http 8000
```

Local, Meta-free validation: POST to `/test-chat` (see `/docs` Swagger UI) with `{"sender_id": "...", "message": "..."}` to exercise the full pipeline without live Instagram credentials.

## Architecture

**Request flow**: `app/webhook/router.py` receives Meta webhook events at `POST /webhook` (GET is used for Meta's verification handshake, checked against `META_VERIFY_TOKEN`). Incoming payloads are validated against `X-Hub-Signature-256` using `META_APP_SECRET` (HMAC-SHA256), then dispatched to `app/webhook/service.py` via FastAPI `BackgroundTasks` — DMs go to `process_incoming_dm`, post comments go to `process_incoming_comment`. Both event types are deduplicated up front using `WebhookLog` (keyed by Meta's message/comment id) before any processing happens.

**Two reply pipelines, one LLM core**: DMs maintain full conversation history (last `max_history_messages` turns from SQLite, config.yaml) and get the full system prompt; comment replies are stateless (no history) and append an instruction to keep replies to ~2 sentences, since they're public. Both pipelines: fetch RAG context via `KnowledgeRetriever.retrieve_context` (currently a no-op stub in `app/knowledge/retriever.py` — Phase 2 will implement Markdown search over `./knowledge_base`), append it to `SYSTEM_PROMPT_NATURAL_MEDICINE` (`app/llm/prompts.py`) when non-empty, call `get_llm_response` (`app/llm/client.py`), and send the reply back to Meta's Graph API (`send_meta_dm` / `send_meta_comment_reply`). LLM failures are caught and replaced with a canned fallback message rather than propagating.

**LLM provider factory**: `app/llm/client.py` reads `config.yaml` (provider base URLs/models, cached via `lru_cache`) and resolves the active provider's API key from `Settings` (`app/config.py`, env-backed via `.env`). `config.yaml`'s `active_provider` selects among `openrouter`/`deepseek`/`openai`; `active_model` overrides the provider's default model if set. All providers are called through the OpenAI-compatible `AsyncOpenAI` client, so adding a new provider only requires an entry under `providers:` plus its API key in `Settings`.

**Persistence**: SQLAlchemy models in `app/models.py` — `Conversation` (keyed by Instagram-scoped user id), `Message` (`sender_type`: `"user"`/`"bot"`, linked to a conversation), `WebhookLog` (dedup ledger for both DMs and comments, shared table). Default DB is `sqlite:///./instagram_bot.db` (`DATABASE_URL` in `.env`); tests spin up an isolated `sqlite:///:memory:` engine (see `tests/test_webhook_service.py` pattern) rather than touching the dev DB file.

**Config split**: secrets and per-environment values live in `.env`/`app/config.py` (`Settings`, pydantic-settings); bot behavior (active LLM provider/model, `bot_name`, `max_history_messages`, `temperature`) lives in `config.yaml`, loaded independently by `app/llm/client.py`. Changing providers or models is a `config.yaml` edit, not a code change.

## Repo conventions

- Business logic and log messages are in Spanish (matches the bot's target audience); keep new code/comments consistent with that where user-facing or domain-specific.
- `docs/superpowers/` holds spec/plan documents from the `superpowers` skill workflow (design docs and implementation plans) — check there for background on why a feature was built a certain way before assuming intent from code alone.
- `docs/meta_setup_guide.md` documents the Meta Developers portal / webhook configuration steps referenced in the README.
