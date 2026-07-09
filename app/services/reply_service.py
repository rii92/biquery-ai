"""LLM-based reply generator — jawaban natural + insight dari data query."""

import json
from typing import Optional

from app.llm.client import LLMClient
from app.core.json_util import serialize_dates


_INTENT_LABELS = {
    "bp_all_kpi_card": "Ringkasan KPI seluruh permohonan izin",
    "bp_flow_permohonan": "Diagram alur/Sankey permohonan izin",
    "bp_tren_inflow_outflow": "Tren inflow (masuk) vs outflow (terbit) per hari",
    "bp_gauge_performa": "Gauge performa penyelesaian permohonan",
    "bp_kepatuhan_sla": "Kepatuhan SLA permohonan izin",
    "bp_funnel_kemacetan": "Analisis kemacetan/funnel per tahapan proses",
    "bp_proporsi_kerja": "Proporsi kerja staf dalam vs luar jam kerja",
    "bp_rapor_staf": "Rapor evaluasi staf (skor akhir, performa, produktivitas, SLA)",
}


async def generate_llm_reply(
    question: str,
    intent: str,
    result: list[dict],
    payload: dict,
    llm_provider: str = "llamacpp",
    timeout: int = 120,
) -> str:
    label = _INTENT_LABELS.get(intent, intent)
    data_json = json.dumps(serialize_dates(result[:20]), indent=2, ensure_ascii=False)
    total_rows = len(result)

    filters = {k: v for k, v in payload.items() if v and k not in ("intent", "_reply")}

    prompt = f"""Kamu adalah asisten analis data warehouse BP Batam. Berikan jawaban yang informatif, analitis, dan mengandung insight.

LAPORAN: {label}
PERTANYAAN: {question}
TOTAL BARIS DATA: {total_rows}

DATA (JSON):
{data_json}

FILTER AKTIF:
{json.dumps(filters, indent=2, ensure_ascii=False) if filters else "Tidak ada filter"}

INSTRUKSI:
1. INTI — Jawab inti laporan dalam 1-2 kalimat pertama.
2. ANGKA — Sebutkan angka-angka penting berikut analisis proporsinya (misal: 60% terbit, 15% masih proses).
3. INSIGHT — Analisis pola dari data:
   - Jika ada yang menonjol (terlalu tinggi/rendah), soroti.
   - Jika ada data SLA/overdue, sebutkan tingkat kepatuhan dan dampaknya.
   - Jika ada tren (inflow vs outflow), sebutkan perbandingan.
   - Jika data staf, sebutkan siapa yang terbaik dan area perbaikan.
4. SARAN — Akhiri dengan 1-2 saran konkret yang bisa ditindaklanjuti.
5. GAYA BAHASA — Bahasa Indonesia natural, tidak kaku, tanpa markdown. Paragraf pendek-pendek.
6. LARANGAN — Jangan mengarang angka. Jika data kosong, bilang data tidak tersedia.
"""

    try:
        llm = LLMClient(provider=llm_provider)
        raw = await llm.generate(prompt, temperature=0.4, max_tokens=1536, timeout=timeout)
        return raw.strip()
    except Exception:
        return ""
