"""API endpoint exposing runtime configuration to the frontend."""
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import OLLAMA_MODEL, BP_DB_HOST, BP_DB_SERVICE_NAME

router = APIRouter()


class ConfigResponse(BaseModel):
    model: str
    bp_host: str
    bp_service: str


@router.get("/api/config", response_model=ConfigResponse)
async def get_config():
    return ConfigResponse(
        model=OLLAMA_MODEL,
        bp_host=BP_DB_HOST,
        bp_service=BP_DB_SERVICE_NAME,
    )
