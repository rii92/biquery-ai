"""FastAPI router for WhatsApp webhook.

All heavy lifting is delegated to services – keeps the API layer thin.
"""
import time

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.intent_service import IntentService
from app.services.database_service import DatabaseService
from app.services.formatter_service import FormatterService

router = APIRouter()

class WhatsAppMessage(BaseModel):
    sender: str
    message: str

intent_service = IntentService()
database_service = DatabaseService()
formatter_service = FormatterService()

@router.post("/webhook/whatsapp")
async def webhook(msg: WhatsAppMessage):
    t0 = time.time()

    payload = intent_service.extract(msg.message)
    intent = payload.get("intent")

    if not intent:
        return {"reply": "Maaf, untuk pertanyaan tersebut data belum tersedia di sistem kami.", "elapsed": round(time.time() - t0, 2)}

    sql = database_service.generate_sql(payload)
    if not database_service.validate_sql(sql):
        return {"reply": "Maaf, pertanyaan tersebut belum didukung sistem.", "elapsed": round(time.time() - t0, 2)}

    result = database_service.execute(sql)
    if not result:
        return {"reply": "Data tidak ditemukan.", "elapsed": round(time.time() - t0, 2)}

    reply = formatter_service.format(payload, result)
    return {"reply": reply, "elapsed": round(time.time() - t0, 2)}
