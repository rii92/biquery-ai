"""API endpoint for the frontend query page.

Returns the generated SQL, raw result, and natural-language reply.
Also provides an SSE endpoint for real-time progress updates.
"""
import json
import time
import asyncio

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.intent_service import IntentService
from app.services.database_service import DatabaseService
from app.services.formatter_service import FormatterService

router = APIRouter()

intent_service = IntentService()
database_service = DatabaseService()
formatter_service = FormatterService()


class QueryRequest(BaseModel):
    message: str
    academic_year: str = ""
    semester: str = ""


class QueryResponse(BaseModel):
    reply: str
    sql: str = ""
    result: list = []
    elapsed: float = 0.0


def _apply_filters(payload: dict, year: str, semester: str) -> dict:
    """Isi academic_year/semester dari dropdown.

    - Semua → string kosong (query tanpa filter year/sem).
    - Spesifik → isi dengan nilai tersebut.
    """
    if year == "Semua":
        payload["academic_year"] = ""
    elif year:
        payload["academic_year"] = year
    if semester == "Semua":
        payload["semester"] = ""
    elif semester:
        payload["semester"] = semester
    return payload


@router.post("/api/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    t0 = time.time()

    payload = intent_service.extract(req.message)
    payload = _apply_filters(payload, req.academic_year, req.semester)
    intent = payload.get("intent")

    if not intent:
        return QueryResponse(reply="Maaf, untuk pertanyaan tersebut data belum tersedia di sistem kami.", elapsed=round(time.time() - t0, 2))

    # Fast path untuk sapaan / off-topic (tanpa SQL)
    if intent == "_greeting":
        reply = payload.get("_reply", "Halo! Ada yang bisa saya bantu?")
        return QueryResponse(reply=reply, elapsed=round(time.time() - t0, 2))

    sql = database_service.generate_sql(payload)
    if not database_service.validate_sql(sql):
        return QueryResponse(
            reply="Maaf, pertanyaan tersebut belum didukung sistem.",
            elapsed=round(time.time() - t0, 2),
        )

    result = database_service.execute(sql)
    if not result:
        return QueryResponse(
            reply="Data tidak ditemukan.", sql=sql, result=[],
            elapsed=round(time.time() - t0, 2),
        )

    reply = formatter_service.format(payload, result)
    return QueryResponse(
        reply=reply, sql=sql, result=result,
        elapsed=round(time.time() - t0, 2),
    )


async def _sse_process(message: str, dropdown_year: str = "", dropdown_semester: str = ""):
    """Generator untuk SSE — yield progress step lalu result."""
    t0 = time.time()

    def _event(data: dict) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    # Step 1
    yield _event({"step": "Menganalisis pertanyaan...", "progress": 10})
    loop = asyncio.get_event_loop()
    payload = await loop.run_in_executor(None, intent_service.extract, message)
    payload = _apply_filters(payload, dropdown_year, dropdown_semester)
    intent = payload.get("intent")

    if not intent:
        yield _event({
            "done": True,
            "reply": "Maaf, untuk pertanyaan tersebut data belum tersedia di sistem kami.",
            "sql": "",
            "result": [],
            "elapsed": round(time.time() - t0, 2),
            "progress": 100,
        })
        return

    # Fast path untuk sapaan / off-topic (tanpa SQL)
    if intent == "_greeting":
        reply = payload.get("_reply", "Halo! Ada yang bisa saya bantu?")
        yield _event({
            "done": True,
            "reply": reply,
            "sql": "",
            "result": [],
            "elapsed": round(time.time() - t0, 2),
            "progress": 100,
        })
        return

    # Step 2
    yield _event({"step": "Menyusun query SQL...", "progress": 30})
    sql = await loop.run_in_executor(None, database_service.generate_sql, payload)

    # Step 3
    yield _event({"step": "Memvalidasi SQL...", "progress": 50})
    valid = await loop.run_in_executor(None, database_service.validate_sql, sql)
    if not valid:
        yield _event({
            "done": True,
            "reply": "Maaf, pertanyaan tersebut belum didukung sistem.",
            "sql": sql,
            "result": [],
            "elapsed": round(time.time() - t0, 2),
            "progress": 100,
        })
        return

    # Step 4
    yield _event({"step": "Menjalankan query ke database...", "progress": 70})
    result = await loop.run_in_executor(None, database_service.execute, sql)
    if not result:
        yield _event({
            "done": True,
            "reply": "Data tidak ditemukan.",
            "sql": sql,
            "result": [],
            "elapsed": round(time.time() - t0, 2),
            "progress": 100,
        })
        return

    # Step 5
    yield _event({"step": "Menyusun jawaban...", "progress": 90})
    reply = await loop.run_in_executor(None, formatter_service.format, payload, result)

    yield _event({
        "done": True,
        "reply": reply,
        "sql": sql,
        "result": result,
        "elapsed": round(time.time() - t0, 2),
        "progress": 100,
    })


@router.get("/api/query/stream")
async def query_stream(
    message: str = Query(..., description="Pertanyaan dalam bahasa alami"),
    academic_year: str = Query("", description="Filter tahun ajaran"),
    semester: str = Query("", description="Filter semester"),
):
    return StreamingResponse(_sse_process(message, academic_year, semester), media_type="text/event-stream")
