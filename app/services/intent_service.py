"""Service intent yang membungkus ekstraktor.

Menyediakan method `extract` yang mengembalikan payload dict
dengan sub-dict `params` diratakan ke level teratas.
"""
from app.ai.intent_extractor import IntentExtractor
from app.core.config import OLLAMA_MODEL as _MODEL


class IntentService:
    def __init__(self, model_name: str = None):
        self.extractor = IntentExtractor(model_name=model_name or _MODEL)

    def extract(self, question: str) -> dict:
        raw = self.extractor.extract(question)
        # Normalisasi "unknown" menjadi intent kosong
        if raw.get("intent") in ("unknown", None):
            raw["intent"] = ""
        # Ratakan params ke level teratas
        params = raw.pop("params", {})
        raw.update(params)
        return raw