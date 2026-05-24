"""Formatter untuk hasil query BP Batam."""

from typing import Any


def _fmt_total_masuk(payload, result):
    if not result:
        return "Data total masuk tidak ditemukan."
    total = sum(r.get("TOTAL_MASUK", 0) for r in result)
    lines = [f"- {r.get('PERIODE', '')}: {r.get('TOTAL_MASUK', 0)} permohonan" for r in result]
    return f"**Total Masuk**: {total} permohonan\n\nRincian per minggu:\n" + "\n".join(lines)


def _fmt_izin_terbit(payload, result):
    if not result:
        return "Data izin terbit tidak ditemukan."
    total = sum(r.get("IZIN_TERBIT", 0) for r in result)
    lines = [f"- {r.get('PERIODE', '')}: {r.get('IZIN_TERBIT', 0)} izin" for r in result]
    return f"**Izin Terbit**: {total} izin\n\nRincian per minggu:\n" + "\n".join(lines)


def _fmt_backlog(payload, result):
    if not result:
        return "Data backlog tidak ditemukan."
    total = sum(r.get("TOTAL_BACKLOG", 0) for r in result)
    lines = [f"- {r.get('PERIODE', '')}: {r.get('TOTAL_BACKLOG', 0)} backlog" for r in result]
    return f"**Total Backlog**: {total} permohonan\n\nRincian per minggu:\n" + "\n".join(lines)


def _fmt_dalam_proses(payload, result):
    if not result:
        return "Tidak ada permohonan dalam proses."
    total = sum(r.get("JUMLAH_PERMOHONAN", 0) for r in result)
    lines = [f"- {r.get('TANGGAL', '')}: {r.get('JUMLAH_PERMOHONAN', 0)} permohonan" for r in result]
    return f"**Dalam Proses**: {total} permohonan\n\nRincian per hari:\n" + "\n".join(lines)


def _fmt_sebaran(payload, result):
    if not result:
        return "Data sebaran izin tidak ditemukan."
    lines = []
    for r in result:
        jenis = r.get("JENIS_IZIN", "")
        status = r.get("KELOMPOK_STATUS", "")
        jumlah = r.get("JUMLAH", 0)
        lines.append(f"- {jenis} — {status}: {jumlah}")
    return "**Sebaran Berdasarkan Jenis Izin**:\n" + "\n".join(lines)


def _fmt_komposisi(payload, result):
    if not result:
        return "Data komposisi status tidak ditemukan."
    groups = {}
    for r in result:
        periode = r.get("PERIODE", "")
        status = r.get("KELOMPOK_STATUS", "")
        jumlah = r.get("JUMLAH", 0)
        if periode not in groups:
            groups[periode] = {}
        groups[periode][status] = groups[periode].get(status, 0) + jumlah
    lines = []
    for periode, statuses in groups.items():
        parts = [f"{s}: {j}" for s, j in statuses.items()]
        lines.append(f"- {periode}: {', '.join(parts)}")
    return "**Komposisi Keseluruhan Status**:\n" + "\n".join(lines)


_FORMATTERS = {
    "bp_total_masuk": _fmt_total_masuk,
    "bp_izin_terbit_per_bulan": _fmt_izin_terbit,
    "bp_total_backlog_per_bulan": _fmt_backlog,
    "bp_dalam_proses": _fmt_dalam_proses,
    "bp_sebaran_jenis_izin": _fmt_sebaran,
    "bp_komposisi_status": _fmt_komposisi,
}


def format_bp_reply(payload: dict, result: list[dict]) -> str:
    intent = payload.get("intent", "")
    formatter = _FORMATTERS.get(intent)
    if formatter:
        return formatter(payload, result)
    return "Maaf, data untuk laporan tersebut belum tersedia."
