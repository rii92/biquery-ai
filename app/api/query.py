"""Unified API endpoint — menangani query BP Batam (Oracle) dan Sekolah (SQLite/MySQL).

Mendeteksi intent source secara otomatis dan merutekan ke database yang sesuai.
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
from app.services.bp_database_service import BPDatabaseService, DatabaseConnectionError
from app.services.bp_formatter_service import format_bp_reply

router = APIRouter()

intent_service = IntentService()
school_service = DatabaseService()
bp_service = BPDatabaseService()
school_formatter = FormatterService()


class QueryRequest(BaseModel):
    message: str
    academic_year: str = ""
    semester: str = ""
    tgl_status_terakhir: str = ""
    perizinan: str = ""
    kategori_status: str = ""


class QueryResponse(BaseModel):
    reply: str
    sql: str = ""
    result: list = []
    elapsed: float = 0.0


def _is_bp(intent: str) -> bool:
    return intent.startswith("bp_")


def _apply_filters(payload: dict, req: QueryRequest) -> dict:
    if _is_bp(payload.get("intent", "")):
        if req.tgl_status_terakhir:
            payload["tgl_status_terakhir"] = req.tgl_status_terakhir
        if req.perizinan:
            payload["perizinan"] = req.perizinan
        if req.kategori_status:
            payload["kategori_status"] = req.kategori_status
    else:
        year = req.academic_year
        semester = req.semester
        if year == "Semua":
            payload["academic_year"] = ""
        elif year:
            payload["academic_year"] = year
        if semester == "Semua":
            payload["semester"] = ""
        elif semester:
            payload["semester"] = semester
    return payload


def _execute(intent: str, payload: dict):
    if _is_bp(intent):
        sql = bp_service.generate_sql(payload)
        if not bp_service.validate_sql(sql):
            return None, sql, []
        try:
            result = bp_service.execute(sql)
        except DatabaseConnectionError as e:
            return f"[ERROR] {e}", sql, []
        reply = format_bp_reply(payload, result) if result else ""
        return reply, sql, result
    else:
        sql = school_service.generate_sql(payload)
        if not school_service.validate_sql(sql):
            return None, sql, []
        result = school_service.execute(sql)
        reply = school_formatter.format(payload, result) if result else ""
        return reply, sql, result


@router.post("/api/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    t0 = time.time()

    payload = intent_service.extract(req.message)
    payload = _apply_filters(payload, req)
    intent = payload.get("intent")

    if not intent:
        return QueryResponse(
            reply="Maaf, untuk pertanyaan tersebut data belum tersedia di sistem kami.",
            elapsed=round(time.time() - t0, 2),
        )

    if intent == "_greeting":
        reply = payload.get("_reply", "Halo! Ada yang bisa saya bantu?")
        return QueryResponse(reply=reply, elapsed=round(time.time() - t0, 2))

    reply, sql, result = _execute(intent, payload)
    if reply is None:
        return QueryResponse(
            reply="Maaf, pertanyaan tersebut belum didukung sistem.",
            sql=sql, elapsed=round(time.time() - t0, 2),
        )
    if reply.startswith("[ERROR]"):
        return QueryResponse(
            reply=reply, sql=sql, result=[],
            elapsed=round(time.time() - t0, 2),
        )
    if not result:
        return QueryResponse(
            reply="Data tidak ditemukan.", sql=sql, result=[],
            elapsed=round(time.time() - t0, 2),
        )

    return QueryResponse(
        reply=reply, sql=sql, result=result,
        elapsed=round(time.time() - t0, 2),
    )


async def _sse_process(req_data: dict):
    """Generator SSE — menerima dict query params."""
    t0 = time.time()

    def _event(data: dict) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    message = req_data.get("message", "")
    if not message:
        yield _event({"done": True, "reply": "Pertanyaan kosong.", "elapsed": 0, "progress": 100})
        return

    yield _event({"step": "Menganalisis pertanyaan...", "progress": 10})
    loop = asyncio.get_event_loop()
    payload = await loop.run_in_executor(None, intent_service.extract, message)
    intent = payload.get("intent")

    if not intent:
        yield _event({
            "done": True,
            "reply": "Maaf, untuk pertanyaan tersebut data belum tersedia di sistem kami.",
            "sql": "", "result": [], "elapsed": round(time.time() - t0, 2), "progress": 100,
        })
        return

    if intent == "_greeting":
        reply = payload.get("_reply", "Halo! Ada yang bisa saya bantu?")
        yield _event({
            "done": True, "reply": reply, "sql": "", "result": [],
            "elapsed": round(time.time() - t0, 2), "progress": 100,
        })
        return

    # Terapkan filter — tiruan dari _apply_filters
    if _is_bp(intent):
        for k in ("tgl_status_terakhir", "perizinan", "kategori_status"):
            v = req_data.get(k, "")
            if v:
                payload[k] = v
    else:
        for k, env_key in [("academic_year", "academic_year"), ("semester", "semester")]:
            v = req_data.get(env_key, "")
            if v == "Semua":
                payload[k] = ""
            elif v:
                payload[k] = v

    yield _event({"step": "Menyusun query SQL...", "progress": 30})
    reply, sql, result = await loop.run_in_executor(None, _execute, intent, payload)

    if reply is None:
        yield _event({
            "done": True,
            "reply": "Maaf, pertanyaan tersebut belum didukung sistem.",
            "sql": sql, "result": [],
            "elapsed": round(time.time() - t0, 2), "progress": 100,
        })
        return

    if reply.startswith("[ERROR]"):
        yield _event({
            "done": True, "reply": reply, "sql": sql, "result": [],
            "elapsed": round(time.time() - t0, 2), "progress": 100,
        })
        return

    yield _event({"step": "Memvalidasi SQL...", "progress": 50})
    if not result:
        yield _event({
            "done": True, "reply": "Data tidak ditemukan.", "sql": sql, "result": [],
            "elapsed": round(time.time() - t0, 2), "progress": 100,
        })
        return

    yield _event({"step": "Menyusun jawaban...", "progress": 90})
    yield _event({
        "done": True, "reply": reply, "sql": sql, "result": result,
        "elapsed": round(time.time() - t0, 2), "progress": 100,
    })


@router.get("/api/query/stream")
async def query_stream(
    message: str = Query(..., description="Pertanyaan dalam bahasa alami"),
    academic_year: str = Query("", description="Filter tahun ajaran (sekolah)"),
    semester: str = Query("", description="Filter semester (sekolah)"),
    tgl_status_terakhir: str = Query("", description="Filter tanggal (BP Batam)"),
    perizinan: str = Query("", description="Filter jenis izin (BP Batam)"),
    kategori_status: str = Query("", description="Filter kategori status (BP Batam)"),
):
    req_data = {
        "message": message,
        "academic_year": academic_year,
        "semester": semester,
        "tgl_status_terakhir": tgl_status_terakhir,
        "perizinan": perizinan,
        "kategori_status": kategori_status,
    }
    return StreamingResponse(_sse_process(req_data), media_type="text/event-stream")
