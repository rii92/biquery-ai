"""Resolves natural language temporal keywords into SQL filter clauses per source/intent."""

import re
from datetime import datetime, timedelta
from typing import Dict

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

    def apply(self, question: str, intent_id: str) -> Dict[str, str]:
        """Resolve temporal keywords and map to intent-specific SQL param clauses.

        Returns:
            Dict like {"filter_tahun": "TAHUN = '2025'", ...}
            ready to be merged into the SQL generation payload.
        """
        standard = self.resolve(question)
        if not standard:
            return {}

        source = intent_id.split("_")[0]
        source_map = SOURCE_PARAM_MAPS.get(source, {})
        intent_map = source_map.get(intent_id, source_map.get("__default__", {}))

        payload = {}

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

        return payload
