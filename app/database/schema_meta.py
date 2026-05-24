"""Metadata skema database untuk prompt LLM.

Menjelaskan struktur setiap tabel dan kolom agar model memahami
hubungan antar tabel saat menulis query SQL.
"""

# Padanan Indonesia untuk setiap kolom (membantu LLM mapping bahasa)
_COLUMN_ALIASES = {
    "students": {"name": "nama", "class": "kelas", "gender": "jenis_kelamin"},
    "teachers": {"name": "nama", "subject": "mata_pelajaran", "gender": "jenis_kelamin"},
    "classrooms": {"class": "kelas", "room_number": "nomor_ruang"},
    "subjects": {"name": "nama", "code": "kode"},
    "grades": {"class": "kelas", "academic_year": "tahun_ajaran", "semester": "semester", "subject": "mata_pelajaran", "score": "nilai"},
    "attendance": {"class": "kelas", "attendance_date": "tanggal", "status": "status", "academic_year": "tahun_ajaran", "semester": "semester"},
    "extracurriculars": {"name": "nama", "coach": "pelatih"},
    "student_extracurriculars": {"academic_year": "tahun_ajaran", "semester": "semester"},
    "homeroom_teachers": {"class": "kelas", "academic_year": "tahun_ajaran", "semester": "semester"},
}


def _col_alias(table: str, col: str) -> str:
    alias = _COLUMN_ALIASES.get(table, {}).get(col, "")
    return f" / {alias}" if alias else ""


SCHEMA_METADATA = [
    {
        "table": "students",
        "description": "Data seluruh siswa",
        "columns": [
            ("id", "INT", "Primary key, auto increment"),
            ("name", "VARCHAR(255)", "Nama lengkap siswa"),
            ("class", "VARCHAR(50)", "Kelas saat ini, contoh: X IPA, XI IPS, XII IPA"),
            ("gender", "VARCHAR(20)", "Jenis kelamin: L (laki-laki) atau P (perempuan)"),
        ],
    },
    {
        "table": "teachers",
        "description": "Data seluruh guru beserta mata pelajaran yang diampu",
        "columns": [
            ("id", "INT", "Primary key, auto increment"),
            ("name", "VARCHAR(255)", "Nama lengkap guru"),
            ("subject", "VARCHAR(100)", "Mata pelajaran yang diampu, contoh: Matematika, Fisika"),
            ("gender", "VARCHAR(1)", "Jenis kelamin: L (laki-laki) atau P (perempuan)"),
        ],
    },
    {
        "table": "classrooms",
        "description": "Data ruang kelas",
        "columns": [
            ("id", "INT", "Primary key, auto increment"),
            ("class", "VARCHAR(50)", "Nama kelas, contoh: X IPA, XI IPS"),
            ("room_number", "VARCHAR(20)", "Nomor ruangan, contoh: R.101"),
        ],
    },
    {
        "table": "subjects",
        "description": "Data mata pelajaran yang diajarkan",
        "columns": [
            ("id", "INT", "Primary key, auto increment"),
            ("name", "VARCHAR(100)", "Nama mata pelajaran, contoh: Matematika, Bahasa Inggris"),
            ("code", "VARCHAR(20)", "Kode mata pelajaran, contoh: MTK, BIG"),
        ],
    },
    {
        "table": "grades",
        "description": "Nilai siswa per mata pelajaran per semester per tahun ajaran",
        "columns": [
            ("id", "INT", "Primary key, auto increment"),
            ("student_id", "INT", "Foreign key ke students.id"),
            ("class", "VARCHAR(50)", "Kelas siswa saat nilai diambil, contoh: X IPA"),
            ("academic_year", "VARCHAR(9)", "Tahun ajaran, contoh: 2023/2024, 2024/2025"),
            ("semester", "VARCHAR(10)", "Semester: Ganjil (semester 1) atau Genap (semester 2)"),
            ("subject", "VARCHAR(100)", "Mata pelajaran, contoh: Matematika, Fisika"),
            ("score", "DECIMAL(5,2)", "Nilai angka, rentang 0 - 100"),
        ],
    },
    {
        "table": "attendance",
        "description": "Data kehadiran siswa per tanggal",
        "columns": [
            ("id", "INT", "Primary key, auto increment"),
            ("student_id", "INT", "Foreign key ke students.id"),
            ("class", "VARCHAR(50)", "Kelas siswa, contoh: X IPA"),
            ("attendance_date", "DATE", "Tanggal pencatatan kehadiran"),
            ("status", "VARCHAR(20)", "Status kehadiran: hadir (masuk), izin (tidak masuk tapi izin), sakit (tidak masuk infokan sakit), alpha (tidak masuk tanpa keterangan)"),
            ("academic_year", "VARCHAR(9)", "Tahun ajaran, contoh: 2023/2024"),
            ("semester", "VARCHAR(10)", "Semester: Ganjil atau Genap"),
        ],
    },
    {
        "table": "extracurriculars",
        "description": "Data kegiatan ekstrakurikuler",
        "columns": [
            ("id", "INT", "Primary key, auto increment"),
            ("name", "VARCHAR(100)", "Nama ekstrakurikuler, contoh: Pramuka, Paskibra, PMR"),
            ("coach", "VARCHAR(255)", "Nama pelatih atau pembina ekstrakurikuler"),
        ],
    },
    {
        "table": "student_extracurriculars",
        "description": "Relasi siswa dengan ekstrakurikuler yang diikuti per semester",
        "columns": [
            ("id", "INT", "Primary key, auto increment"),
            ("student_id", "INT", "Foreign key ke students.id"),
            ("extracurricular_id", "INT", "Foreign key ke extracurriculars.id"),
            ("academic_year", "VARCHAR(9)", "Tahun ajaran, contoh: 2023/2024"),
            ("semester", "VARCHAR(10)", "Semester: Ganjil atau Genap"),
        ],
    },
    {
        "table": "homeroom_teachers",
        "description": "Data penempatan wali kelas per kelas per semester",
        "columns": [
            ("id", "INT", "Primary key, auto increment"),
            ("teacher_id", "INT", "Foreign key ke teachers.id (guru yang menjadi wali kelas)"),
            ("class", "VARCHAR(50)", "Kelas yang diampu, contoh: X IPA"),
            ("academic_year", "VARCHAR(9)", "Tahun ajaran, contoh: 2023/2024"),
            ("semester", "VARCHAR(10)", "Semester: Ganjil atau Genap"),
        ],
    },
]


def build_schema_section() -> str:
    """Bangun blok skema database untuk prompt LLM (dengan alias Indonesia)."""
    lines = []
    for tbl in SCHEMA_METADATA:
        tname = tbl["table"]
        lines.append(f"  - {tname}: {tbl['description']}")
        for col_name, col_type, col_desc in tbl["columns"]:
            alias = _col_alias(tname, col_name)
            lines.append(f"    - {col_name}{alias} ({col_type}): {col_desc}")
        lines.append("")
    return "\n".join(lines)
