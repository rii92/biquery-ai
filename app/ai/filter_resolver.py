"""Resolves natural language temporal keywords into SQL filter clauses per source/intent."""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Optional

from app.intents.loader import get_intent

logger = logging.getLogger("filter_resolver")

MONTH_NAMES = {
    "januari": "01", "februari": "02", "maret": "03",
    "april": "04", "mei": "05", "juni": "06",
    "juli": "07", "agustus": "08", "september": "09",
    "oktober": "10", "november": "11", "desember": "12",
}

MONTH_PATTERN = '|'.join(MONTH_NAMES.keys())

IZIN_PATTERNS = [
    (r'\bPB\s*UMKU\b', "SUB_JENIS_IZIN", "PB UMKU"),
    (r'\bPB\s*PERSEROAN\b', "SUB_JENIS_IZIN", "PB PERSEROAN"),
    (r'\bPB\s*PERORANGAN\b', "SUB_JENIS_IZIN", "PB PERORANGAN"),
    (r'\bPL\s*PERSEROAN\b', "SUB_JENIS_IZIN", "PL PERSEROAN"),
    (r'\bPL\s*PERORANGAN\b', "SUB_JENIS_IZIN", "PL PERORANGAN"),
    (r'\bPB\b', "JENIS_IZIN", "PB"),
    (r'\bPL\b', "JENIS_IZIN", "PL"),
    (r'\bLALIN\b', "JENIS_IZIN", "LALIN"),
]

STATUS_KEYWORDS = [
    (r'\bterbit\b', "TERBIT"),
    (r'\bdisetujui\b', "TERBIT"),
    (r'\btolak\b', "TOLAK"),
    (r'\bditolak\b', "TOLAK"),
    (r'\bdalam\s+proses\b', "DALAM PROSES"),
    (r'\bproses\s+pelaku\s+usaha\b', "PROSES PELAKU USAHA"),
    (r'\bcabut\b', "CABUT"),
    (r'\bdicabut\b', "CABUT"),
]


def _get_filter_mappings(intent_id: str) -> dict:
    """Load filter_mappings from intents.json for the given intent."""
    meta = get_intent(intent_id)
    return (meta or {}).get("filter_mappings", {})


def _validate_mappings(mappings: dict, intent_id: str):
    """Log warning for mapping keys whose param doesn't exist in intent."""
    meta = get_intent(intent_id)
    if not meta:
        return
    intent_params = set(meta.get("params", {}).keys())
    for key, fm in mappings.items():
        if fm["param"] not in intent_params:
            logger.warning(
                "filter_mappings[%s].param='%s' not found in intent %s params",
                key, fm["param"], intent_id,
            )


class FilterResolver:
    """Detect temporal keywords from user question and map to SQL filter params."""

    def resolve(self, question: str) -> Dict[str, str]:
        """Extract standardized temporal filters from a natural language question.

        Returns:
            Dict with keys: tahun, bulan, tanggal_awal, tanggal_akhir (when detected)
        """
        filters = {}
        q = question.lower().strip()

        if re.search(r'tahun\s+(ini|sekarang)', q):
            filters["tahun"] = str(datetime.now().year)

        m = re.search(r'tahun\s+(\d{4})', q)
        if m:
            filters["tahun"] = m.group(1)

        if re.search(r'bulan\s+(ini|sekarang)', q):
            filters["bulan"] = f"{datetime.now().month:02d}"

        m = re.search(
            rf'(?:bulan\s+)?({MONTH_PATTERN})\s*(\d{{4}})?',
            q
        )
        if m:
            filters["bulan"] = MONTH_NAMES[m.group(1)]
            if m.group(2):
                filters["tahun"] = m.group(2)

        m = re.search(r'(\d+)\s+(tahun|bulan|hari)\s+terakhir', q)
        if m:
            num = int(m.group(1))
            unit = m.group(2)
            now = datetime.now()
            if unit == "tahun":
                from_date = now.replace(year=now.year - num, month=1, day=1)
            elif unit == "bulan":
                month = now.month - num
                year = now.year
                while month < 1:
                    month += 12
                    year -= 1
                from_date = now.replace(year=year, month=month, day=1)
            else:
                from_date = now - timedelta(days=num)
            filters["tanggal_awal"] = from_date.strftime("%Y-%m-%d")
            filters["tanggal_akhir"] = now.strftime("%Y-%m-%d")

        return filters

    def resolve_entities(self, question: str) -> Dict[str, str]:
        """Extract non-temporal entities (izin type, status) from question."""
        entities = {}
        q_upper = question.upper()

        for pattern, etype, value in IZIN_PATTERNS:
            if re.search(pattern, q_upper):
                entities["perizinan"] = value
                entities["izin_column"] = etype
                break

        for pattern, status in STATUS_KEYWORDS:
            if re.search(pattern, question.lower()):
                entities["kategori_status"] = status
                break

        return entities

    def map_to_sql(self, standard_filters: dict, intent_id: str) -> dict:
        """Map standard filter keys to SQL clause payload using filter_mappings.

        Args:
            standard_filters: dict like {"tahun": "2026", "perizinan": "PB"}
            intent_id: target intent

        Returns:
            Dict of SQL param → SQL clause ready for payload merge.
        """
        mappings = _get_filter_mappings(intent_id)
        payload = {}

        for key, value in standard_filters.items():
            if key in mappings:
                fm = mappings[key]
                param = fm["param"]
                sql = fm["sql"].replace("{value}", str(value))
                payload[param] = sql

        return payload

    def apply(self, question: str, intent_id: str) -> Dict[str, str]:
        """Resolve temporal keywords + entities, map to intent-specific SQL clauses.

        This is the sync (regex-based) version.
        For LLM-based extraction, use resolve_via_llm() instead.

        Returns:
            Dict of SQL param → SQL clause ready to be merged into payload.
        """
        mappings = _get_filter_mappings(intent_id)
        _validate_mappings(mappings, intent_id)

        standard = self.resolve(question)
        entities = self.resolve_entities(question)

        all_filters = {**standard, **entities}
        return self.map_to_sql(all_filters, intent_id)

    async def resolve_via_llm(self, question: str, intent_id: str) -> dict:
        """Async: use LLM to extract structured filter values from question.

        Returns dict of standard filter keys → values, e.g.:
        {"tahun": "2026", "perizinan": "PB", "kategori_status": "TOLAK"}

        Falls back to empty dict if LLM unavailable or parsing fails.
        """
        mappings = _get_filter_mappings(intent_id)
        if not mappings:
            return {}

        from app.llm.client import LLMClient

        meta = get_intent(intent_id)
        intent_params = (meta or {}).get("params", {})

        lines = []
        for key, fm in mappings.items():
            desc = intent_params.get(fm["param"], key)
            example_val = _example_value(key)
            example_sql = fm["sql"].replace("{value}", example_val)
            lines.append(f"- \"{key}\": {desc} (contoh SQL: {example_sql})")

        filters_text = "\n".join(lines)

        prompt = (
            f"Extract filter values from this question about BP Batam data.\n\n"
            f"Available filters for this query type:\n"
            f"{filters_text}\n\n"
            f"Question: {question}\n\n"
            f"Return ONLY a JSON object with the extracted filter keys and values.\n"
            f'Example: {{"tahun": "2026", "perizinan": "PB"}}\n'
            f"If a filter is not mentioned in the question, OMIT it from the JSON.\n"
            f"Only use keys from the available filters list above.\n"
            f"Return ONLY the raw JSON, no explanation, no markdown."
        )

        try:
            llm = LLMClient(provider="llamacpp")
            raw = await llm.generate(prompt, temperature=0.1, max_tokens=256, timeout=30)
            raw = raw.strip()
            # Try to find and parse JSON
            match = re.search(r"\{[\s\S]*\}", raw)
            if not match:
                logger.warning("resolve_via_llm: no JSON found in response: %.100s", raw)
                return {}

            extracted = json.loads(match.group())

            if not isinstance(extracted, dict):
                return {}

            # Validate — only keep keys that are in this intent's filter_mappings
            valid = {}
            for k, v in extracted.items():
                if k in mappings:
                    valid[k] = str(v)
                else:
                    logger.warning("resolve_via_llm: unknown key '%s' for intent %s", k, intent_id)

            if valid:
                logger.info("resolve_via_llm OK — extracted %d filter(s): %s", len(valid), valid)
            return valid

        except json.JSONDecodeError as e:
            logger.warning("resolve_via_llm: JSON parse error: %s", e)
        except Exception as e:
            logger.warning("resolve_via_llm failed: %s", e)

        return {}


def _example_value(key: str) -> str:
    """Return a plausible example value for a filter key (for LLM prompt)."""
    examples = {
        "tahun": "2026",
        "bulan": "01",
        "tanggal_awal": "2026-01-01",
        "tanggal_akhir": "2026-12-31",
        "perizinan": "PB",
        "kategori_status": "TERBIT",
    }
    return examples.get(key, "<nilai>")
