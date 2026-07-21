import logging
import time

from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.keyword_classifier import classify_by_keyword, is_blacklisted, is_followup, is_affirmative, needs_context
from app.ai.embedding_classifier import classify_by_embedding
from app.ai.filter_resolver import FilterResolver
from app.services.bp_database_service import BPDatabaseService, DatabaseConnectionError
from app.services.bp_formatter_service import format_bp_reply
from app.services.insight_service import InsightService
from app.services.reply_service import generate_llm_reply
from app.core.memory import get_memory, MAX_EXCHANGES_BEFORE_RESET

logger = logging.getLogger("webhook")

router = APIRouter()


class WhatsAppMessage(BaseModel):
    sender: str
    message: str


bp_service = BPDatabaseService()


_NO_DATA_SUGGESTIONS = (
    "Data tidak ditemukan. Coba pertanyaan lain:\n"
    "\u2022 Berapa total perizinan?\n"
    "\u2022 Berapa nilai SLA?\n"
    "\u2022 Berapa kinerja perizinan?\n"
    "\u2022 Siapa staf yang paling produktif?\n"
    "\u2022 Bagaimana tren inflow outflow?"
)

_MAX_FOLLOWUP_EXCEEDED = (
    f"Percakapan sudah mencapai {MAX_EXCHANGES_BEFORE_RESET} kali. "
    "Silakan mulai dengan pertanyaan baru."
)


@router.get("/webhook/health")
async def webhook_health():
    """Diagnostik: test koneksi ke Ornith dari dalam container."""
    import httpx
    from app.core.config import LLAMACPP_API_URL, LLAMACPP_MODEL
    from openai import AsyncOpenAI

    result = {"ornith_api_url": LLAMACPP_API_URL, "ornith_model": LLAMACPP_MODEL}

    # Test 1: HTTP GET /v1/models
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{LLAMACPP_API_URL}/models")
            result["http_models"] = {"status": r.status_code, "ok": r.status_code == 200}
    except Exception as e:
        result["http_models"] = {"status": "error", "error": str(e)}

    # Test 2: Chat completion dummy
    try:
        client = AsyncOpenAI(api_key="sk-no-key-required", base_url=LLAMACPP_API_URL, timeout=10)
        resp = await client.chat.completions.create(
            model=LLAMACPP_MODEL,
            messages=[{"role": "user", "content": "Katakan halo dalam 1 kata"}],
            temperature=0.1,
            max_tokens=10,
        )
        result["chat_test"] = {"status": "ok", "reply": resp.choices[0].message.content.strip()}
    except Exception as e:
        result["chat_test"] = {"status": "error", "error": str(e)}

    return result


@router.post("/webhook/whatsapp")
async def webhook(msg: WhatsAppMessage):
    t0 = time.time()
    memory = get_memory()
    session_id = f"wa_{msg.sender}"

    # ── QA Fix 1 & 3: Auto-reset memory if max exchanges reached ──
    if memory.check_and_reset(session_id):
        # If user sends a follow-up after reset, tell them to start fresh
        if is_followup(msg.message) or needs_context(msg.message):
            return {"reply": _MAX_FOLLOWUP_EXCEEDED, "elapsed": round(time.time() - t0, 2)}

    history = memory.get_history(session_id)

    # Step 1-2: Blacklist + Keyword
    if is_blacklisted(msg.message):
        return {"reply": "Maaf, pertanyaan mengandung perintah yang tidak diizinkan.", "elapsed": round(time.time() - t0, 2)}
    payload = classify_by_keyword(msg.message) or {"intent": ""}
    intent = payload.get("intent")

    # Step 3: Greeting
    if intent == "_greeting":
        return {"reply": payload.get("_reply", "Halo!"), "elapsed": round(time.time() - t0, 2)}

    # Step 3.5: Follow-up / needs-context
    if not intent and history:
        is_follow = is_followup(msg.message)
        needs_ctx = needs_context(msg.message)
        if is_follow or needs_ctx:
            last = history[-1]
            if is_follow and not is_affirmative(msg.message):
                return {"reply": "Baik, ada pertanyaan lain yang bisa saya bantu?", "elapsed": round(time.time() - t0, 2)}
            logger.info("Follow-up dari user=%s (follow=%s, ctx=%s), reuse intent=%s",
                        msg.sender, is_follow, needs_ctx, last.intent)
            payload = {
                "intent": last.intent,
                **last.payload,
            }
            intent = last.intent

    # Step 4: Embedding Classifier (fallback)
    if not intent:
        emb = classify_by_embedding(msg.message)
        if emb:
            payload = emb
            intent = payload["intent"]

    if not intent:
        return {"reply": "Maaf, untuk pertanyaan tersebut data belum tersedia di sistem kami.", "elapsed": round(time.time() - t0, 2)}

    # Step 5: FilterResolver (sync regex + async LLM)
    if intent not in ("_greeting",):
        is_follow = is_followup(msg.message)
        needs_ctx = needs_context(msg.message)
        if not ((is_follow or needs_ctx) and history):
            resolver = FilterResolver()

            # Try LLM-based filter extraction first (async)
            llm_filters = await resolver.resolve_via_llm(msg.message, intent)
            if llm_filters:
                # If status filter is extracted but intent doesn't support it, it's silently ignored
                resolved = resolver.map_to_sql(llm_filters, intent)
                if resolved:
                    payload.update(resolved)
                    logger.info("LLM filter extraction applied: %s", llm_filters)

            # Also apply regex-based extraction as fallback/supplement
            regex_resolved = resolver.apply(msg.message, intent)
            if regex_resolved:
                # Merge but don't overwrite LLM results
                for k, v in regex_resolved.items():
                    if k not in payload or not payload.get(k):
                        payload[k] = v

    sql = bp_service.generate_sql(payload)
    if not sql or not bp_service.validate_sql(sql):
        return {"reply": "Maaf, pertanyaan tersebut belum didukung sistem.", "elapsed": round(time.time() - t0, 2)}

    try:
        result = bp_service.execute(sql)
    except DatabaseConnectionError:
        return {"reply": "Maaf, database sedang tidak tersedia. Silakan coba lagi nanti.", "elapsed": round(time.time() - t0, 2)}

    if not result:
        return {"reply": _NO_DATA_SUGGESTIONS, "elapsed": round(time.time() - t0, 2)}

    det_insight = InsightService().deterministic(payload, result)

    # Coba llamacpp dulu, fallback ke local, terakhir deterministic
    reply = ""
    for prov in ("llamacpp", "local"):
        logger.info("Mencoba LLM provider=%s untuk intent=%s", prov, intent)
        reply = await generate_llm_reply(msg.message, intent, result, payload, llm_provider=prov, timeout=120, history=history)
        if reply:
            logger.info("Berhasil pakai provider=%s \u2014 %d chars", prov, len(reply))
            break
        logger.warning("Provider=%s gagal, coba provider berikutnya", prov)

    if not reply:
        logger.warning("Semua LLM gagal, fallback ke format deterministik")
        reply = format_bp_reply(payload, result)

    memory.add(session_id, msg.message, reply, intent, sql, payload)

    return {"reply": reply, "elapsed": round(time.time() - t0, 2)}
