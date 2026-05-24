"""Ekstraksi intent menggunakan Ollama + cadangan kata kunci.

Mengirim pertanyaan user ke API Ollama lokal dengan prompt
terstruktur (dibangun dinamis dari prompts/intents.json) dan
mengembalikan payload JSON berisi intent + slot.
Jika model mengembalikan unknown atau intent tidak valid, fallback
ke pengklasifikasi kata kunci deterministik.
"""
import json
import re
from typing import Any, Dict

import httpx

from app.core.config import OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_TIMEOUT
from app.ai.keyword_classifier import classify_by_keyword
from app.intents.loader import build_prompt_section, build_params_section, build_examples_section
from app.database.schema_meta import build_schema_section

PROMPT_TEMPLATE = """Anda adalah sistem klasifikasi intent.

Tugas:
- Identifikasi intent dari daftar berikut.
- Ekstrak parameter yang relevan.
- Jawab HANYA dengan JSON, **tanpa markdown, tanpa teks lain, tanpa komentar**.

Format JSON yang HARUS diikuti:
{{"intent": "<nama_intent>", "params": {{"<key>": "<value>"}}}}

PENTING: Gunakan nama intent PERSIS seperti di daftar. Jangan membuat nama intent baru.

DAFTAR INTENT:
{intents}

PARAMETER (hanya ekstrak jika relevan):
{params}

SKEMA DATABASE (untuk referensi):
{schema}

CONTOH:
{examples}

Jika pertanyaan TIDAK cocok dengan intent mana pun:
{{"intent": "unknown", "params": {{}}}}

Pertanyaan: {question}
"""


class IntentExtractor:
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or OLLAMA_MODEL
        self.api_url = f"{OLLAMA_HOST}/api/generate"

    def _build_prompt(self, question: str) -> str:
        return PROMPT_TEMPLATE.format(
            intents=build_prompt_section(),
            params=build_params_section(),
            schema=build_schema_section(),
            examples=build_examples_section(),
            question=question,
        )

    def _parse_json(self, raw: str) -> Dict[str, Any] | None:
        """Try to parse JSON from LLM response, stripping surrounding text."""
        raw = raw.strip()
        # hapus markdown code fences jika ada
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip()
        # cari { pertama dan } terakhir
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            raw = raw[start : end + 1]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def extract(self, question: str) -> Dict[str, Any]:
        # 1. Pengklasifikasi kata kunci dulu (cepat, deterministik)
        fallback = classify_by_keyword(question)
        if fallback is not None:
            return fallback

        # 2. LLM sebagai cadangan untuk pertanyaan kompleks
        prompt = self._build_prompt(question)
        try:
            resp = httpx.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=OLLAMA_TIMEOUT,
            )
            resp.raise_for_status()
            raw = resp.json().get("response", "")
            parsed = self._parse_json(raw)
            if parsed is not None and parsed.get("intent") not in (None, "", "unknown", "none"):
                return parsed
        except Exception:
            pass

        return {"intent": "unknown"}
