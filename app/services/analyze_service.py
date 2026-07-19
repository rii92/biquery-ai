"""Generate insight & recommendation from query + answer using LLM."""

import json
import logging

from app.llm.client import LLMClient

logger = logging.getLogger("analyze_service")


async def generate_insight_recommendation(
    query: str,
    output_jawaban: str,
    template_output_jawaban: str = "",
    llm_provider: str = "llamacpp",
) -> dict:
    prompt = f"""Anda adalah asisten analis data. Berdasarkan pertanyaan dan jawaban di bawah, buatlah insight singkat dan satu rekomendasi praktis.

PERTANYAAN:
{query}

JAWABAN SISTEM:
{output_jawaban}

TEMPLATE FORMAT YANG DIGUNAKAN:
{template_output_jawaban}

INSTRUKSI:
- Insight: jelaskan temuan utama, pola, atau hal menarik dari jawaban di atas (1-2 kalimat).
- Rekomendasi: saran tindakan praktis berdasarkan insight tersebut (1 kalimat).
- Jawab dalam bahasa Indonesia.
- Kembalikan HANYA dalam format JSON valid tanpa markdown, tanpa kutip tambahan:
{{"insight": "...", "rekomendasi": "..."}}
"""

    try:
        llm = LLMClient(provider=llm_provider)
        raw = await llm.generate(prompt, temperature=0.3, max_tokens=1024)
        raw = raw.strip()

        # Bersihkan wrapping markdown code block jika ada
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
