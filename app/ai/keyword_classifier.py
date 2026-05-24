from typing import Dict, Any
import re
from app.core.config import ACADEMIC_YEARS

_DEFAULT_YEAR = ACADEMIC_YEARS[0] if ACADEMIC_YEARS else "2024/2025"
_DEFAULT_SEMESTER = "Ganjil"

_KELAS_MAP = {"10": "X", "x": "X", "11": "XI", "xi": "XI", "12": "XII", "xii": "XII"}
_JURUSAN = ["IPA", "IPS"]

_SUBJECT_ALIASES = {
    "matematika": "Matematika", "mtk": "Matematika",
    "fisika": "Fisika",
    "biologi": "Biologi",
    "kimia": "Kimia",
    "bahasa indonesia": "Bahasa Indonesia", "indonesia": "Bahasa Indonesia", "bin": "Bahasa Indonesia",
    "bahasa inggris": "Bahasa Inggris", "inggris": "Bahasa Inggris", "big": "Bahasa Inggris",
    "sejarah": "Sejarah", "sjh": "Sejarah",
    "geografi": "Geografi", "geo": "Geografi",
    "ekonomi": "Ekonomi", "eko": "Ekonomi",
    "olahraga": "Olahraga", "olr": "Olahraga",
}

_EXTRACURRICULAR_ALIASES = {
    "paskibra": "Paskibra", "pramuka": "Pramuka", "pmr": "PMR",
    "rohis": "Rohis", "basket": "Basket", "futsal": "Futsal",
    "seni tari": "Seni Tari", "pks": "PKS",
}


def _normalise_kelas(raw: str) -> str:
    parts = raw.split()
    if not parts:
        return raw
    first = _KELAS_MAP.get(parts[0], parts[0]).upper()
    rest = parts[1].upper() if len(parts) > 1 else ""
    result = f"{first} {rest}"
    if rest in _JURUSAN:
        return result
    return result.strip()


def _extract_subject(q: str) -> str:
    for alias, canonical in _SUBJECT_ALIASES.items():
        if alias in q:
            return canonical
    return ""


def _extract_extracurricular(q: str) -> str:
    for alias, canonical in _EXTRACURRICULAR_ALIASES.items():
        if alias in q:
            return canonical
    return "Paskibra"


def _extract_names(raw: str) -> list:
    """Extract one or more names connected by 'dan', 'atau', or ','."""
    parts = re.split(r"\s+(?:dan|atau)\s+|\s*,\s*", raw)
    return [p.strip().capitalize() for p in parts if p.strip()]


def _extract_year(q: str) -> str:
    m = re.search(r"(\d{4}/\d{4})", q)
    return m.group(1) if m else _DEFAULT_YEAR


# ── Main classifier ──────────────────────────────────────────────────

def classify_by_keyword(question: str) -> Dict[str, Any] | None:
    q = question.lower().strip()

    # ── SAPAAN / OFF-TOPIC (fast path, tanpa LLM) ────────────────────

    if re.search(r"\b(kamu|lu|kau|anda)\s*(siapa|ini)", q):
        return {"intent": "_greeting", "_reply": "Aku adalah <b>EduQuery AI</b>, asisten tanya-jawab data sekolah. Tanyakan soal siswa, guru, nilai, ekstrakurikuler, atau kehadiran!"}

    if re.search(r"\b(halo|hai|hey|hi|selamat\s+\w+)\b", q):
        return {"intent": "_greeting", "_reply": "Halo! Ada yang bisa saya bantu tentang data sekolah? Coba tanya jumlah siswa, nilai, atau wali kelas."}

    if re.search(r"\b(terima\s*kasih|makasih|thanks|trims)\b", q):
        return {"intent": "_greeting", "_reply": "Sama-sama! Senang bisa membantu."}

    if re.search(r"\b(siapa\s*nama|namamu|nama\s*kamu)\b", q):
        return {"intent": "_greeting", "_reply": "Namaku <b>EduQuery AI</b>! Aku siap membantu menjawab pertanyaan seputar data sekolah."}

    # ── SISWA ────────────────────────────────────────────────────────

    # jumlah siswa berdasarkan nama (bisa ganda: "Maya dan Dewi")
    m = re.search(r"(?:jumlah|banyak|berapa).*(?:namanya|nama|bernama|dipanggil)\s+(.+?)(?:\?|$)", q)
    if m:
        names = _extract_names(m.group(1).strip())
        if len(names) == 1:
            return {"intent": "count_students_by_name", "nama": names[0]}
        extra = " OR ".join(f"name LIKE '%{n}%'" for n in names[1:])
        return {"intent": "count_students_by_name", "nama": names[0], "extra_nama_clause": f" OR {extra}"}

    # cari siswa berdasarkan nama (bisa ganda)
    m = re.search(r"(?:cari|siapa|nama).*(?:namanya|bernama|dipanggil)\s+(.+?)(?:\?|$)", q)
    if m:
        names = _extract_names(m.group(1).strip())
        if len(names) == 1:
            return {"intent": "list_students_by_name", "nama": names[0]}
        extra = " OR ".join(f"name LIKE '%{n}%'" for n in names[1:])
        return {"intent": "list_students_by_name", "nama": names[0], "extra_nama_clause": f" OR {extra}"}

    # siswa tidak hadir / alpha (daftar atau hitung)
    if re.search(r"(?:tidak\s+(?:hadir|masuk)|alpha|absen|bolos|mangkir)", q):
        kelas = ""
        m = re.search(r"(?:kelas|class)\s+(\w+\s*\w*)", q)
        if m:
            kelas = _normalise_kelas(m.group(1).strip().upper())
        if re.search(r"\b(siapa|daftar|nama)\b", q):
            return {"intent": "list_alpha_students", "kelas": kelas}
        return {"intent": "class_attendance", "kelas": kelas}

    # jumlah siswa per kelas per tahun
    if re.search(r"(?:jumlah|banyak).*(?:siswa|kelas).*(?:tahun|angkatan|ajaran)", q):
        return {"intent": "count_students_per_class_per_year"}

    # jumlah / filter siswa + gender
    m = re.search(r"(?:jumlah|banyak|per).*(?:siswa|kelas).*(?:jenis.kelamin|gender|laki|perempuan)", q)
    if m:
        return {"intent": "count_students_gender_per_class"}

    # siswa + gender (daftar)
    m = re.search(r"(?:daftar|siapa|nama|tampilkan).*(?:siswa|murid).*(laki|perempuan|pria|wanita)", q)
    if m:
        gender = "L" if m.group(1) in ("laki", "pria") else "P"
        return {"intent": "list_students_gender", "gender": gender}

    # jumlah siswa + gender
    m = re.search(r"(?:jumlah|banyak|berapa).*(?:siswa|murid).*(laki|perempuan|pria|wanita)", q)
    if m:
        gender = "L" if m.group(1) in ("laki", "pria") else "P"
        return {"intent": "count_students_gender", "gender": gender}

    # jumlah siswa (tanpa filter lain)
    if re.search(r"(?:jumlah|banyak|berapa).*siswa", q):
        return {"intent": "count_students"}

    # daftar siswa per kelas
    m = re.search(r"(?:siswa|murid|peserta\s+didik).*(?:kelas|class)\s+(\w+\s*\w*)", q)
    if m:
        kelas = _normalise_kelas(m.group(1).strip().upper())
        return {"intent": "list_students", "kelas": kelas}

    # ── GURU ─────────────────────────────────────────────────────────

    # guru + mapel
    m = re.search(r"(?:guru|pengajar).*(matematika|fisika|biologi|kimia|bahasa|inggris|indonesia|sejarah|geografi|ekonomi|olahraga)", q)
    if m:
        subject = _extract_subject(q)
        return {"intent": "teacher_by_subject", "subject": subject}

    # guru + gender
    m = re.search(r"(?:daftar|siapa|nama).*guru.*(?:laki|perempuan|pria|wanita)", q)
    if m:
        gender = "L" if re.search(r"laki|pria", q) else "P"
        return {"intent": "list_teachers_gender", "gender": gender}

    # jumlah guru
    if re.search(r"(?:jumlah|banyak).*guru", q):
        return {"intent": "count_teachers"}

    # daftar guru (tanpa filter mapel/gender)
    if re.search(r"(?:daftar|siapa|nama).*guru", q):
        return {"intent": "list_teachers"}

    # ── WALI KELAS ─────────────────────────────────────────────────

    if re.search(r"wali\s*kelas", q):
        m = re.search(r"(?:kelas|class)\s+(\w+\s*\w*)", q)
        kelas = _normalise_kelas(m.group(1).strip().upper()) if m else "X IPA"
        return {"intent": "homeroom_teacher", "kelas": kelas, "academic_year": _DEFAULT_YEAR}

    # ── MAPEL ────────────────────────────────────────────────────────

    if re.search(r"(?:daftar|\bapa\b|mapel|pelajaran|mata\s*pelajaran)", q) and not re.search(r"(?:guru|nilai|siswa|wali|rata)", q):
        return {"intent": "list_subjects"}

    # ── NILAI ────────────────────────────────────────────────────────

    # rata-rata terendah per kelas (cek sebelum average_score_per_class_by_subject)
    if re.search(r"(?:terendah|paling\s+rendah)", q) and re.search(r"(?:rata-?rata|nilai)", q) and re.search(r"(?:per\s+kelas|tiap\s+kelas)", q):
        subject = _extract_subject(q)
        result = {"intent": "lowest_average_per_class", "academic_year": _extract_year(q)}
        if subject:
            result["subject"] = subject
        return result

    # rata-rata per kelas per mapel
    m = re.search(r"(?:rata-?rata|rerata)\s*(?:nilai|score)?\s+(\w+)\s+tiap\s+kelas", q)
    if m:
        subject = _extract_subject(q) or m.group(1).strip().capitalize()
        return {"intent": "average_score_per_class_by_subject", "subject": subject, "academic_year": _extract_year(q)}

    # rata-rata per kelas
    m = re.search(r"(?:rata-?rata|rerata)\s*(?:nilai|score)?\s*(?:kelas|angkatan)\s+(\w+\s*\w*)", q)
    if m:
        kelas = _normalise_kelas(m.group(1).strip().upper())
        return {"intent": "class_average_score", "kelas": kelas}

    # rata-rata terendah per kelas
    if re.search(r"(?:terendah|paling\s+rendah)", q) and re.search(r"(?:rata-?rata|nilai)", q) and re.search(r"(?:per\s+kelas|tiap\s+kelas)", q):
        subject = _extract_subject(q)
        result = {"intent": "lowest_average_per_class", "academic_year": _extract_year(q)}
        if subject:
            result["subject"] = subject
        return result

    # rata-rata siswa
    m = re.search(r"(?:rata-?rata|rerata|nilai\s+rata)\s*(?:nilai|score)?\s*(\w+)", q)
    if m:
        name = m.group(1).strip().capitalize()
        return {"intent": "student_average_score", "name": name, "academic_year": _DEFAULT_YEAR, "semester": _DEFAULT_SEMESTER}

    # nilai tertinggi / top
    if re.search(r"(?:tertinggi|terbaik|paling\s+tinggi|top|juara)", q):
        subject = _extract_subject(q) or "Matematika"
        return {"intent": "top_students", "subject": subject, "academic_year": _DEFAULT_YEAR, "semester": _DEFAULT_SEMESTER}

    # siswa lulus / tuntas
    if re.search(r"(?:lulus|tuntas|pass|diatas\s*KKM|lolos)", q):
        subject = _extract_subject(q)
        return {"intent": "count_students_pass", "subject": subject}

    # ── EKSTRAKURIKULER ───────────────────────────────────────

    m = re.search(r"(?:ekskul|ekstrakurikuler|paskibra|pramuka|pmr|rohis|basket|futsal|seni\s*tari|pks)", q)
    if m:
        ekstra = _extract_extracurricular(q)
        return {"intent": "student_extracurriculars", "extracurricular": ekstra}

    return None
