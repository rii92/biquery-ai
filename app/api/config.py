"""API endpoint exposing runtime configuration to the frontend."""
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import OLLAMA_MODEL, ACADEMIC_YEARS

router = APIRouter()


class ConfigResponse(BaseModel):
    model: str
    academic_years: list[str]
    semesters: list[str]


@router.get("/api/config", response_model=ConfigResponse)
async def get_config():
    return ConfigResponse(
        model=OLLAMA_MODEL,
        academic_years=ACADEMIC_YEARS,
        semesters=["Ganjil", "Genap"],
    )
