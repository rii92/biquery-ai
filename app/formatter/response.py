import re
from typing import Dict, Any, List, Callable


def _counted(result, fallback="Data tidak ditemukan.") -> int:
    return result[0].get("count", 0) if result else 0


def _list_entries(result, fmt=lambda r: f"- {r['name']}", fallback="Data tidak ditemukan.") -> str:
    if not result:
        return fallback
    entries = [fmt(r) for r in result]
    return "\n".join(entries)


# ── Formatters ───────────────────────────────────────────────────────

_formatters: Dict[str, Callable] = {}

def _grouped(result, fmt=lambda y, s, v: f"{y} {s}: {v}", fallback="Data tidak ditemukan.") -> str:
    if not result:
        return fallback
    lines = []
    for r in result:
        y = r.get("academic_year", "")
        s = r.get("semester", "")
        lines.append(fmt(y, s, r))
    return "\n".join(lines)


def _fmt(payload, result):
    if not result:
        return "Data tidak ditemukan."
    kelas = payload.get("kelas")
    prefix = f"Di kelas {kelas}:\n" if kelas else ""
    lines = [f"- {r['academic_year']} {r['semester']}: {r['count']} siswa" for r in result]
    return prefix + "\n".join(lines)
_formatters["count_students"] = _fmt

def _fmt(payload, result):
    if not result:
        return "Data tidak ditemukan."
    lines = [f"- {r['name']} ({r['class']}) — {r.get('academic_year','')} {r.get('semester','')}" for r in result]
    return "\n".join(lines)
_formatters["list_students"] = _fmt

def _fmt(payload, result):
    count = _counted(result)
    return f"Ada {count} guru di sekolah."
_formatters["count_teachers"] = _fmt

def _fmt(payload, result):
    return _list_entries(result, fmt=lambda r: f"- {r['name']}", fallback="Data tidak ditemukan.")
_formatters["list_teachers"] = _fmt

def _fmt(payload, result):
    label = "laki-laki" if payload.get("gender") == "L" else "perempuan"
    return _list_entries(result, fmt=lambda r: f"- {r['name']} ({r.get('subject', '')})", fallback="Data tidak ditemukan.")
_formatters["list_teachers_gender"] = _fmt

def _fmt(payload, result):
    count = _counted(result)
    label = "laki-laki" if payload.get("gender") == "L" else "perempuan"
    return f"Siswa {label} ada {count} orang."
_formatters["count_students_gender"] = _fmt

def _fmt(payload, result):
    if not result:
        return "Data tidak ditemukan."
    lines = [f"- {r['name']} — {r.get('academic_year','')} {r.get('semester','')}" for r in result]
    return "\n".join(lines)
_formatters["teacher_by_subject"] = _fmt

def _fmt(payload, result):
    return _list_entries(result, fmt=lambda r: f"- {r['name']}", fallback="Data tidak ditemukan.")
_formatters["list_subjects"] = _fmt

def _fmt(payload, result):
    label = "laki-laki" if payload.get("gender") == "L" else "perempuan"
    return _list_entries(result, fmt=lambda r: f"- {r['name']} ({r['class']})", fallback="Data tidak ditemukan.")
_formatters["list_students_gender"] = _fmt

def _fmt(payload, result):
    if not result:
        return "Data tidak ditemukan."
    if len(result) == 1 and result[0].get("academic_year"):
        avg = result[0]["average"]
        name = payload.get("name", "")
        y = result[0]["academic_year"]
        s = result[0]["semester"]
        return f"Nilai rata-rata {name} ({y} {s}) adalah {float(avg):.2f}."
    lines = [f"- {r['academic_year']} {r['semester']}: {float(r['average']):.2f}" for r in result if r.get('average') is not None]
    name = payload.get("name", "")
    return f"Nilai rata-rata {name}:\n" + "\n".join(lines)
_formatters["student_average_score"] = _fmt

def _fmt(payload, result):
    if not result or result[0].get("score") is None:
        return "Data tidak ditemukan."
    lines = [f"- {r['name']} ({r['class']}) — {r['score']}" for r in result]
    return "Nilai tertinggi:\n" + "\n".join(lines)
_formatters["top_students"] = _fmt

def _fmt(payload, result):
    if not result:
        return "Tidak ada siswa yang tidak hadir."
    lines = [f"- {r['academic_year']} {r['semester']}: {r['count']} siswa" for r in result]
    return "Siswa tidak hadir:\n" + "\n".join(lines)
_formatters["class_attendance"] = _fmt

def _fmt(payload, result):
    if not result:
        return "Wali kelas tidak ditemukan."
    line = f"Wali kelas {payload.get('kelas', '')}: "
    if len(result) == 1:
        r = result[0]
        return line + f"{r['name']} ({r['academic_year']} {r['semester']})"
    lines = [f"- {r['academic_year']} {r['semester']}: {r['name']}" for r in result]
    return line + "\n" + "\n".join(lines)
_formatters["homeroom_teacher"] = _fmt

def _fmt(payload, result):
    return _list_entries(result, fmt=lambda r: f"- {r['name']} ({r['class']})", fallback="Belum ada peserta.")
_formatters["student_extracurriculars"] = _fmt

def _fmt(payload, result):
    if not result:
        return "Data tidak ditemukan."
    lines = [f"- {r['name']} ({r['class']}) — {r.get('academic_year','')} {r.get('semester','')}" for r in result]
    return "\n".join(lines)
_formatters["list_students_gender"] = _fmt

def _fmt(payload, result):
    if not result:
        return "Data nilai tidak ditemukan."
    lines = [f"- {r['name']} ({r['class']}) — {r.get('score','')} ({r.get('academic_year','')} {r.get('semester','')})" for r in result]
    return "Nilai tertinggi:\n" + "\n".join(lines)
_formatters["top_students"] = _fmt

def _fmt(payload, result):
    if not result:
        return "Belum ada peserta."
    lines = [f"- {r['name']} ({r['class']}) — {r.get('academic_year','')} {r.get('semester','')}" for r in result]
    return "\n".join(lines)
_formatters["student_extracurriculars"] = _fmt

def _fmt(payload, result):
    label = "laki-laki" if payload.get("gender") == "L" else "perempuan"
    if not result:
        return f"Tidak ada siswa {label}."
    lines = [f"- {r['academic_year']} {r['semester']}: {r['count']} {label}" for r in result]
    return f"Siswa {label}:\n" + "\n".join(lines)
_formatters["count_students_gender"] = _fmt

def _fmt(payload, result):
    if not result:
        return "Data tidak ditemukan."
    lines = [f"- {r['academic_year']} {r['semester']}: {r['count']}" for r in result]
    return f"Jumlah {payload.get('class','')} per kelas:\n" + "\n".join(lines)
_formatters["count_students_gender_per_class"] = _fmt

def _fmt(payload, result):
    return _list_entries(result, fmt=lambda r: f"- {r['class']} ({r['academic_year']}): {r['count']} siswa", fallback="Data tidak ditemukan.")
_formatters["count_students_per_class_per_year"] = _fmt

def _fmt(payload, result):
    if not result:
        return "Data tidak ditemukan."
    lines = [f"- {row['class']}: {float(row['average']):.2f} ({row.get('academic_year','')} {row.get('semester','')})" for row in result if row.get('average') is not None]
    return f"Rata-rata nilai {payload.get('subject', '')}:\n" + "\n".join(lines)
_formatters["average_score_per_class_by_subject"] = _fmt

def _fmt(payload, result):
    if not result:
        return "Data tidak ditemukan."
    lines = [f"- {row['class']}: {row['name']} ({float(row['average']):.2f}) — {row.get('academic_year','')} {row.get('semester','')}" for row in result]
    subject = payload.get('subject', '')
    prefix = f"Nilai rata-rata {subject} terendah per kelas:\n" if subject else "Nilai rata-rata terendah per kelas:\n"
    return prefix + "\n".join(lines)
_formatters["lowest_average_per_class"] = _fmt

def _fmt(payload, result):
    if not result:
        return "Data tidak ditemukan."
    lines = [f"- {r.get('academic_year','')} {r.get('semester','')}: {r['name']} ({float(r['average']):.2f})" for r in result]
    return f"Rata-rata nilai kelas {payload.get('kelas', '')}:\n" + "\n".join(lines)
_formatters["class_average_score"] = _fmt


def format_reply(payload: Dict[str, Any], result: List[Dict[str, Any]]) -> str:
    intent = payload.get("intent", "")
    formatter = _formatters.get(intent)
    if formatter:
        return formatter(payload, result)
    return "Maaf, untuk pertanyaan tersebut data belum tersedia di sistem kami."


# ── Formatter untuk intent baru ─────────────────────────────────────

def _fmt(payload, result):
    if not result:
        nama = payload.get("nama", "")
        extra = payload.get("extra_nama_clause", "")
        if extra:
            extra_names = re.findall(r"LIKE '%([^']+)%'", extra)
            label = " atau ".join([nama] + extra_names)
            return f"Tidak ada siswa bernama {label}."
        return f"Tidak ada siswa yang namanya {nama}."
    lines = [f"- {r['academic_year']} {r['semester']}: {r['count']} siswa" for r in result]
    return "\n".join(lines)
_formatters["count_students_by_name"] = _fmt

def _fmt(payload, result):
    if not result:
        return "Data tidak ditemukan."
    lines = [f"- {r['name']} ({r['class']}) — {r.get('academic_year','')} {r.get('semester','')}" for r in result]
    return "\n".join(lines)
_formatters["list_students_by_name"] = _fmt

def _fmt(payload, result):
    return _list_entries(result, fmt=lambda r: f"- {r['name']} — {r['coach']}", fallback="Data tidak ditemukan.")
_formatters["list_extracurriculars"] = _fmt

def _fmt(payload, result):
    return _list_entries(result, fmt=lambda r: f"- {r['class']} ({r['room_number']})", fallback="Data tidak ditemukan.")
_formatters["list_classes"] = _fmt

def _fmt(payload, result):
    count = _counted(result)
    label = "laki-laki" if payload.get("gender") == "L" else "perempuan"
    return f"Ada {count} guru {label}."
_formatters["count_teachers_gender"] = _fmt

def _fmt(payload, result):
    if not result:
        return "Data tidak ditemukan."
    status = payload.get("status", "")
    lines = [f"- {r['academic_year']} {r['semester']}: {r['count']} siswa" for r in result]
    return f"Siswa dengan status '{status}':\n" + "\n".join(lines)
_formatters["attendance_by_status"] = _fmt

def _fmt(payload, result):
    return _list_entries(result, fmt=lambda r: f"- {r['name']}: {r['status']} ({r.get('academic_year','')} {r.get('semester','')})", fallback="Tidak ada data kehadiran.")
_formatters["attendance_detail"] = _fmt

def _fmt(payload, result):
    if not result:
        return "Tidak ditemukan."
    lines = [f"- {r['name']} ({r['class']}) — {r['average']} ({r.get('academic_year','')} {r.get('semester','')})" for r in result]
    return "Rata-rata tertinggi:\n" + "\n".join(lines)
_formatters["top_students_overall"] = _fmt

def _fmt(payload, result):
    if not result:
        return "Semua siswa hadir, tidak ada yang alpha."
    lines = [f"- {r['name']} ({r['class']}) — {r.get('academic_year','')} {r.get('semester','')}" for r in result]
    return "Siswa yang tidak hadir (alpha):\n" + "\n".join(lines)
_formatters["list_alpha_students"] = _fmt
