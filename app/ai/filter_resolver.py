"""Resolves natural language temporal keywords into SQL filter clauses per source/intent."""

import re
from datetime import datetime, timedelta
from typing import Dict

from app.intents.loader import get_intent

MONTH_NAMES = {
    "januari": "01", "februari": "02", "maret": "03",
    "april": "04", "mei": "05", "juni": "06",
    "juli": "07", "agustus": "08", "september": "09",
    "oktober": "10", "november": "11", "desember": "12",
}

SOURCE_PARAM_MAPS = {
    "bp": {
        "bp_all_kpi_card": {
            "tahun": ("tahun", "TO_CHAR(TGL_STATUS_TERAKHIR, 'YYYY') = '{v}'"),
            "bulan": ("bulan", "TO_CHAR(TGL_STATUS_TERAKHIR, 'MM') = '{v}'"),
            "tanggal_awal": ("tgl_status_terakhir", "TRUNC(TGL_STATUS_TERAKHIR) >= TO_DATE('{v}','YYYY-MM-DD')"),
            "tanggal_akhir": ("tgl_status_terakhir", "TRUNC(TGL_STATUS_TERAKHIR) <= TO_DATE('{v}','YYYY-MM-DD')"),
        },
        "__default__": {
            "tahun": ("filter_tahun", "TAHUN = '{v}'"),
            "bulan": ("filter_bulan", "BULAN = '{v}'"),
            "tanggal_awal": ("rentang_tgl_masuk", "TGL_MASUK >= TO_DATE('{v}','YYYY-MM-DD')"),
            "tanggal_akhir": ("rentang_tgl_masuk", "TGL_MASUK <= TO_DATE('{v}','YYYY-MM-DD')"),
        },
    },
    "oss": {
        "__default__": {
            "tahun": ("filter_tahun", "TAHUN = '{v}'"),
            "bulan": ("filter_bulan", "BULAN = '{v}'"),
            "tanggal_awal": ("rentang_tgl_masuk", "TGL_MASUK >= TO_DATE('{v}','YYYY-MM-DD')"),
            "tanggal_akhir": ("rentang_tgl_masuk", "TGL_MASUK <= TO_DATE('{v}','YYYY-MM-DD')"),
        },
    },
    "iboss": {
        "__default__": {
            "tahun": ("pilih_tahun", "TO_CHAR(TX_PERMOHONAN.TGL_DAFTAR, 'YYYY') = '{v}'"),
            "bulan": ("pilih_bulan", "TO_CHAR(TX_PERMOHONAN.TGL_DAFTAR, 'FMMM') = '{v}'"),
            "tanggal_awal": ("rentang_waktu", "TX_PERMOHONAN.TGL_DAFTAR >= TO_DATE('{v}','YYYY-MM-DD')"),
            "tanggal_akhir": ("rentang_waktu", "TX_PERMOHONAN.TGL_DAFTAR <= TO_DATE('{v}','YYYY-MM-DD')"),
        },
        "iboss_rata_waktu_role": {
            "tahun": ("pilih_tahun", "TO_CHAR(T_LOG_LICENSING.ACTION_TIME, 'YYYY') = '{v}'"),
            "bulan": ("pilih_bulan", "TO_CHAR(T_LOG_LICENSING.ACTION_TIME, 'FMMM') = '{v}'"),
            "tanggal_awal": ("rentang_waktu", "T_LOG_LICENSING.ACTION_TIME >= TO_DATE('{v}','YYYY-MM-DD')"),
            "tanggal_akhir": ("rentang_waktu", "T_LOG_LICENSING.ACTION_TIME <= TO_DATE('{v}','YYYY-MM-DD')"),
        },
    },
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
                entities["izin_type"] = value
                entities["izin_column"] = etype
                break

        for pattern, status in STATUS_KEYWORDS:
            if re.search(pattern, question.lower()):
                entities["status"] = status
                break

        return entities

    def apply(self, question: str, intent_id: str) -> Dict[str, str]:
        """Resolve temporal keywords + entities, map to intent-specific SQL clauses.

        Returns:
            Dict of SQL param → SQL clause ready to be merged into payload.
        """
        source = intent_id.split("_")[0]
        source_map = SOURCE_PARAM_MAPS.get(source, {})
        intent_map = source_map.get(intent_id, source_map.get("__default__", {}))

        meta = get_intent(intent_id)
        intent_params = meta.get("params", {}) if meta else {}

        payload = {}

        # ── Temporal filters ──
        standard = self.resolve(question)
        if "tahun" in standard and "tahun" in intent_map:
            param, template = intent_map["tahun"]
            payload[param] = template.replace("{v}", standard["tahun"])

        if "bulan" in standard and "bulan" in intent_map:
            param, template = intent_map["bulan"]
            payload[param] = template.replace("{v}", standard["bulan"])

        rentang_parts = []
        if "tanggal_awal" in standard and "tanggal_awal" in intent_map:
            param, template = intent_map["tanggal_awal"]
            rentang_parts.append(template.replace("{v}", standard["tanggal_awal"]))
        if "tanggal_akhir" in standard and "tanggal_akhir" in intent_map:
            param, template = intent_map["tanggal_akhir"]
            rentang_parts.append(template.replace("{v}", standard["tanggal_akhir"]))
        if rentang_parts:
            target = intent_map.get("tanggal_awal", intent_map.get("tanggal_akhir"))[0]
            payload[target] = " AND ".join(rentang_parts)

        # ── Entity filters (izin type, status) ──
        entities = self.resolve_entities(question)

        if "izin_type" in entities:
            izin = entities["izin_type"]
            col = entities.get("izin_column", "JENIS_IZIN")

            if "perizinan" in intent_params:
                payload["perizinan"] = f"UPPER(JENIS_IZIN) = UPPER('{izin}')"
            elif "pilih_izin" in intent_params:
                if source == "bp":
                    payload["pilih_izin"] = f"(UPPER(JENIS_IZIN) = UPPER('{izin}') OR UPPER(KATEGORI_IZIN_LALIN) = UPPER('{izin}'))"
                else:
                    payload["pilih_izin"] = f"UPPER({col}) = UPPER('{izin}')"
            elif "pilih_sub_izin" in intent_params and col == "SUB_JENIS_IZIN":
                payload["pilih_sub_izin"] = f"UPPER({col}) = UPPER('{izin}')"
            elif "pilih_izin_iboss" in intent_params:
                payload["pilih_izin_iboss"] = f"UPPER(TX_PERMOHONAN.KATEGORI_IZIN) = UPPER('{izin}')"

        if "status" in entities:
            status = entities["status"]
            if "kategori_status" in intent_params:
                payload["kategori_status"] = f"KATEGORI_STATUS = '{status}'"

        return payload
