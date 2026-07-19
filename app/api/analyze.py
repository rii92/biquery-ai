from fastapi import APIRouter
from pydantic import BaseModel

from app.services.analyze_service import generate_insight_recommendation

router = APIRouter()


class AnalyzeRequest(BaseModel):
    query: str
    output_jawaban: str
    template_output_jawaban: str = ""
    llm_provider: str = "llamacpp"


class AnalyzeResponse(BaseModel):
    jawaban_insight: str
    jawaban_rekomendasi: str


@router.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    result = await generate_insight_recommendation(
        query=req.query,
        output_jawaban=req.output_jawaban,
        template_output_jawaban=req.template_output_jawaban,
        llm_provider=req.llm_provider,
    )
    return AnalyzeResponse(**result)
