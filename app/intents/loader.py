"""Memuat dan mengelola intent dari prompts/intents.json."""
import json
from pathlib import Path
from typing import Any, Dict, List

INTENTS_FILE = Path(__file__).resolve().parent.parent.parent / "prompts" / "intents.json"


def _read() -> List[Dict[str, Any]]:
    with open(INTENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _write(data: List[Dict[str, Any]]):
    with open(INTENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def list_intents() -> List[Dict[str, Any]]:
    return _read()


def get_intent(intent_id: str) -> Dict[str, Any] | None:
    for item in _read():
        if item["id"] == intent_id:
            return item
    return None


def create_intent(data: Dict[str, Any]) -> Dict[str, Any]:
    intents = _read()
    # Generate ID otomatis dari deskripsi jika tidak disediakan
    if "id" not in data or not data["id"]:
        base = data.get("description", "new_intent").lower().replace(" ", "_")[:30]
        data["id"] = base
    # Pastikan ID unik
    ids = {i["id"] for i in intents}
    original = data["id"]
    counter = 1
    while data["id"] in ids:
        data["id"] = f"{original}_{counter}"
        counter += 1
    data.setdefault("params", {})
    data.setdefault("examples", [])
    data.setdefault("active", True)
    intents.append(data)
    _write(intents)
    return data


def update_intent(intent_id: str, data: Dict[str, Any]) -> Dict[str, Any] | None:
    intents = _read()
    for i, item in enumerate(intents):
        if item["id"] == intent_id:
            item.update(data)
            item["id"] = intent_id  # pertahankan ID asli
            intents[i] = item
            _write(intents)
            return item
    return None


def delete_intent(intent_id: str) -> bool:
    intents = _read()
    new_list = [i for i in intents if i["id"] != intent_id]
    if len(new_list) == len(intents):
        return False
    _write(new_list)
    return True


def build_prompt_section() -> str:
    """Bangun blok DAFTAR INTENT untuk prompt LLM."""
    intents = _read()
    lines = []
    for item in intents:
        if item.get("active", True):
            lines.append(f"- {item['id']}: {item['description']}")
    return "\n".join(lines)


def build_params_section() -> str:
    """Bangun blok PARAMETER untuk prompt LLM."""
    all_params: Dict[str, str] = {}
    for item in _read():
        if item.get("active", True):
            for param, desc in item.get("params", {}).items():
                if param not in all_params:
                    all_params[param] = desc
    lines = []
    for name, desc in all_params.items():
        lines.append(f"- {name}: {desc}")
    return "\n".join(lines)


def build_examples_section() -> str:
    """Bangun blok CONTOH dengan contoh dari setiap intent."""
    intents = _read()
    lines = []
    for item in intents:
        if not item.get("active", True):
            continue
        examples = item.get("examples", [])
        if not examples:
            continue
        params_list = list(item.get("params", {}).keys())
        if not params_list:
            lines.append(f'Pertanyaan: "{examples[0]}"')
            lines.append(f'Jawaban: {{"intent": "{item["id"]}", "params": {{}}}}')
        else:
            example_params = ", ".join(f'"{p}": "<value>"' for p in params_list)
            lines.append(f'Pertanyaan: "{examples[0]}"')
            lines.append(f'Jawaban: {{"intent": "{item["id"]}", "params": {{{example_params}}}}}')
    return "\n".join(lines)
