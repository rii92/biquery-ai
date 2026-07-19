"""Generate insight & recommendation from query + answer using LLM."""

import json
import logging

from app.llm.client import LLMClient

logger = logging.getLogger("analyze_service")


async def generate_insight_recommendation(
    query: str,
    output_jawaban: str,
    template_output_jawaban: str = "",
    template_output_rekomendasi: str = "",
    llm_provider: str = "llamacpp",
) -> dict:
    data_json = output_jawaban
    if isinstance(output_jawaban, (list, dict)):
        data_json = json.dumps(output_jawaban, indent=2, ensure_ascii=False)

    prompt = f"""Anda adalah asisten analis data. Berdasarkan SQL query dan hasil query di bawah, buatlah insight singkat dan satu rekomendasi praktis.

SQL QUERY:
{query}

HASIL QUERY:
{data_json}

TEMPLATE INSIGHT:
{template_output_jawaban}

TEMPLATE REKOMENDASI:
{template_output_rekomendasi}

INSTRUKSI:
- Insight: jelaskan temuan utama, pola, atau hal menarik dari hasil query di atas sesuai template insight (1-2 kalimat).
- Rekomendasi: saran tindakan praktis berdasarkan insight tersebut sesuai template rekomendasi (1 kalimat).
- Jawab dalam bahasa Indonesia.
- Kembalikan HANYA dalam format JSON valid tanpa markdown, tanpa kutip tambahan:
{{"insight": "...", "rekomendasi": "..."}}
"""

    try:
        llm = LLMClient(provider=llm_provider)
        raw = await llm.generate(prompt, temperature=0.3, max_tokens=1024)
        raw = raw.strip()

        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            raw = raw.rsplit("\n```", 1)[0]

        parsed = json.loads(raw)
        insight = str(parsed.get("insight", "")).strip()
        rekomendasi = str(parsed.get("rekomendasi", "")).strip()
        logger.info("generate_insight_recommendation OK — %d chars insight, %d chars rekomendasi", len(insight), len(rekomendasi))
        return {"jawaban_insight": insight, "jawaban_rekomendasi": rekomendasi}

    except (json.JSONDecodeError, KeyError, Exception) as e:
        logger.warning("generate_insight_recommendation GAGAL — %s", e)
        return {"jawaban_insight": "", "jawaban_rekomendasi": ""}
