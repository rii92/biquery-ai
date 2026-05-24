import random
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

from app.core.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_IS_LOCAL, SQLITE_PATH, ACADEMIC_YEARS


def _mysql_url() -> str:
    user = quote_plus(DB_USER)
    pw = quote_plus(DB_PASSWORD)
    return f"mysql+pymysql://{user}:{pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def _get_engine():
    if DB_IS_LOCAL:
        db_path = Path(__file__).resolve().parent.parent.parent / SQLITE_PATH
        return create_engine(f"sqlite:///{db_path}")
    return create_engine(_mysql_url())


def wait_for_db():
    engine = _get_engine()
    if DB_IS_LOCAL:
        return engine
    for i in range(30):
        try:
            conn = engine.connect()
            conn.close()
            return engine
        except Exception:
            time.sleep(1)
    raise RuntimeError("MySQL tidak bisa dihubungi setelah 30 detik")


# ── DDL ──────────────────────────────────────────────────────────────

_TABLES = [
    "extracurriculars", "subjects", "classrooms", "teachers",
    "students", "homeroom_teachers", "student_extracurriculars",
    "attendance", "grades",
]

def _ddl() -> list[str]:
    ai = "INTEGER PRIMARY KEY AUTOINCREMENT" if DB_IS_LOCAL else "INT NOT NULL AUTO_INCREMENT PRIMARY KEY"
    fk = "" if DB_IS_LOCAL else " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
    return [
        f"CREATE TABLE extracurriculars (id {ai}, name VARCHAR(100) NOT NULL UNIQUE, coach VARCHAR(255)){fk};",
        f"CREATE TABLE subjects (id {ai}, name VARCHAR(100) NOT NULL UNIQUE, code VARCHAR(20)){fk};",
        f"CREATE TABLE classrooms (id {ai}, class VARCHAR(50) NOT NULL UNIQUE, room_number VARCHAR(20)){fk};",
        f"CREATE TABLE teachers (id {ai}, name VARCHAR(255) NOT NULL, subject VARCHAR(100) NOT NULL, gender VARCHAR(1) NOT NULL DEFAULT 'L'){fk};",
        f"CREATE TABLE students (id {ai}, name VARCHAR(255) NOT NULL, class VARCHAR(50) NOT NULL, gender VARCHAR(20) NOT NULL){fk};",
        f"CREATE TABLE homeroom_teachers (id {ai}, teacher_id INT NOT NULL, class VARCHAR(50) NOT NULL, academic_year VARCHAR(9) NOT NULL, semester VARCHAR(10) NOT NULL, FOREIGN KEY (teacher_id) REFERENCES teachers(id)){fk};",
        f"CREATE TABLE student_extracurriculars (id {ai}, student_id INT NOT NULL, extracurricular_id INT NOT NULL, academic_year VARCHAR(9) NOT NULL, semester VARCHAR(10) NOT NULL, FOREIGN KEY (student_id) REFERENCES students(id), FOREIGN KEY (extracurricular_id) REFERENCES extracurriculars(id)){fk};",
        f"CREATE TABLE attendance (id {ai}, student_id INT NOT NULL, class VARCHAR(50) NOT NULL, attendance_date DATE NOT NULL, status VARCHAR(20) NOT NULL, academic_year VARCHAR(9) NOT NULL, semester VARCHAR(10) NOT NULL, FOREIGN KEY (student_id) REFERENCES students(id)){fk};",
        f"CREATE TABLE grades (id {ai}, student_id INT NOT NULL, class VARCHAR(50) NOT NULL, academic_year VARCHAR(9) NOT NULL, semester VARCHAR(10) NOT NULL, subject VARCHAR(100) NOT NULL, score DECIMAL(5,2) NOT NULL, FOREIGN KEY (student_id) REFERENCES students(id)){fk};",
    ]


def _fk_off(conn):
    if not DB_IS_LOCAL:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))


def _fk_on(conn):
    if not DB_IS_LOCAL:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))


def run_migration(engine):
    with engine.begin() as conn:
        _fk_off(conn)
        for tbl in reversed(_TABLES):
            conn.execute(text(f"DROP TABLE IF EXISTS {tbl}"))
        for ddl in _ddl():
            conn.execute(text(ddl))
        _fk_on(conn)
    print("[migrate] Tabel dibuat ulang (drop + create)")


# ── Seed data ─────────────────────────────────────────────────────────

GENDERS = ["L", "P"]
SEMESTERS = ["Ganjil", "Genap"]

random.seed(42)

CLASSES = ["X IPA", "X IPS", "XI IPA", "XI IPS", "XII IPA", "XII IPS"]

TEACHERS = [
    ("Siti Rahmawati", "Matematika", "P"),
    ("Ahmad Fauzi", "Fisika", "L"),
    ("Dewi Sartika", "Biologi", "P"),
    ("Budi Santoso", "Kimia", "L"),
    ("Rina Amelia", "Bahasa Indonesia", "P"),
    ("Agus Wijaya", "Bahasa Inggris", "L"),
    ("Fitri Handayani", "Sejarah", "P"),
    ("Hendra Gunawan", "Geografi", "L"),
    ("Nurul Hidayah", "Ekonomi", "P"),
    ("Rudi Hartono", "Olahraga", "L"),
]

SUBJECTS = [
    ("Matematika", "MTK"), ("Fisika", "FIS"), ("Biologi", "BIO"),
    ("Kimia", "KIM"), ("Bahasa Indonesia", "BIN"), ("Bahasa Inggris", "BIG"),
    ("Sejarah", "SJH"), ("Geografi", "GEO"), ("Ekonomi", "EKO"), ("Olahraga", "OLR"),
]

CLASSROOMS = [(c, f"R.{i+101}") for i, c in enumerate(CLASSES)]

EXTRACURRICULARS = [
    ("Paskibra", "Hendra Gunawan"), ("Pramuka", "Agus Wijaya"),
    ("PMR", "Rina Amelia"), ("Rohis", "Nurul Hidayah"),
    ("Basket", "Rudi Hartono"), ("Futsal", "Ahmad Fauzi"),
    ("Seni Tari", "Dewi Sartika"), ("PKS", "Fitri Handayani"),
]

STUDENT_NAMES = [
    "Adi Pratama", "Budi Hartono", "Citra Ayu Dewi", "Dian Permata Sari", "Eko Prasetyo",
    "Fitriani Hasanah", "Gilang Ramadhan", "Hesti Purnama Sari", "Indra Lesmana", "Keanu Arjuna",
    "Kartika Sari", "Lukman Hakim", "Mega Utami", "Novi Andriani", "Rafa Athallah",
    "Putri Maulida", "Qori Aisyah", "Rizky Pratama", "Sari Dewi", "Gibran Akbar",
    "Umi Kalsum", "Vina Octavia", "Wahyu Nugroho", "Xena Permata", "Keysha Amora",
    "Naura Adinda", "Kenzie Aditya", "Saskia Aurelia", "Shanum Azalea", "Zhafira Azzahra",
]

STUDENT_GENDERS = {
    "Adi Pratama": "L", "Budi Hartono": "L", "Citra Ayu Dewi": "P", "Dian Permata Sari": "P", "Eko Prasetyo": "L",
    "Fitriani Hasanah": "P", "Gilang Ramadhan": "L", "Hesti Purnama Sari": "P", "Indra Lesmana": "L", "Keanu Arjuna": "L",
    "Kartika Sari": "P", "Lukman Hakim": "L", "Mega Utami": "P", "Novi Andriani": "P", "Rafa Athallah": "L",
    "Putri Maulida": "P", "Qori Aisyah": "P", "Rizky Pratama": "L", "Sari Dewi": "P", "Gibran Akbar": "L",
    "Umi Kalsum": "P", "Vina Octavia": "P", "Wahyu Nugroho": "L", "Xena Permata": "P", "Keysha Amora": "P",
    "Naura Adinda": "P", "Kenzie Aditya": "L", "Saskia Aurelia": "P", "Shanum Azalea": "P", "Zhafira Azzahra": "P",
}


def _tab(name, cols):
    return f"INSERT INTO {name} ({','.join(cols)}) VALUES "


def _vals(rows):
    def fmt(v):
        if isinstance(v, str):
            return "'" + v.replace("'", "''") + "'"
        if isinstance(v, float):
            return f"{v:.2f}"
        return str(v)
    return ",\n".join("(" + ",".join(fmt(c) for c in row) + ")" for row in rows)


# Student cohorts: not all students are active from the start
#   2023/2024 → students 1-24
#   2024/2025 → +3 (25-27) → 27 total
#   2025/2026 → +3 (28-30) → 30 total
def _active_ids(year: str) -> range:
    if year == ACADEMIC_YEARS[0]:
        return range(1, 25)
    if year == ACADEMIC_YEARS[1]:
        return range(1, 28)
    return range(1, 31)


def seed(engine):
    stmts = [
        _tab("teachers", ["name", "subject", "gender"]) + _vals(TEACHERS) + ";",
        _tab("classrooms", ["class", "room_number"]) + _vals(CLASSROOMS) + ";",
        _tab("subjects", ["name", "code"]) + _vals(SUBJECTS) + ";",
        _tab("extracurriculars", ["name", "coach"]) + _vals(EXTRACURRICULARS) + ";",
    ]

    student_data = [(name, CLASSES[i % len(CLASSES)], STUDENT_GENDERS[name]) for i, name in enumerate(STUDENT_NAMES)]
    stmts.append(_tab("students", ["name", "class", "gender"]) + _vals(student_data) + ";")

    grade_data = []
    for year in ACADEMIC_YEARS:
        for sem in SEMESTERS:
            for sid in _active_ids(year):
                chosen = random.sample([s[0] for s in SUBJECTS], 5)
                for subj in chosen:
                    score = round(random.uniform(55, 100), 1)
                    cls = student_data[sid - 1][1]
                    grade_data.append((sid, cls, year, sem, subj, score))
    stmts.append(_tab("grades", ["student_id", "class", "academic_year", "semester", "subject", "score"]) + _vals(grade_data) + ";")

    att_statuses = ["hadir", "hadir", "hadir", "alpha", "sakit", "izin"]
    att_data = []
    base_date = date(2024, 1, 10)
    for year_idx, year in enumerate(ACADEMIC_YEARS):
        active = list(_active_ids(year))
        for sem in SEMESTERS:
            for offset in range(3):
                d = base_date + timedelta(days=year_idx * 365 + offset * 30)
                for sid in random.sample(active, min(8, len(active))):
                    cls = student_data[sid - 1][1]
                    status = random.choice(att_statuses)
                    att_data.append((sid, cls, d.isoformat(), status, year, sem))
    stmts.append(_tab("attendance", ["student_id", "class", "attendance_date", "status", "academic_year", "semester"]) + _vals(att_data) + ";")

    se_data = []
    for year in ACADEMIC_YEARS:
        for sem in SEMESTERS:
            for sid in _active_ids(year):
                if random.random() < 0.4:
                    se_data.append((sid, random.randint(1, len(EXTRACURRICULARS)), year, sem))
    stmts.append(_tab("student_extracurriculars", ["student_id", "extracurricular_id", "academic_year", "semester"]) + _vals(se_data) + ";")

    ht_data = []
    for year in ACADEMIC_YEARS:
        for sem in SEMESTERS:
            for cls_i, cls in enumerate(CLASSES):
                ht_data.append(((cls_i % len(TEACHERS)) + 1, cls, year, sem))
    stmts.append(_tab("homeroom_teachers", ["teacher_id", "class", "academic_year", "semester"]) + _vals(ht_data) + ";")

    with engine.begin() as conn:
        for stmt in stmts:
            conn.execute(text(stmt))

    print("[migrate] Seed data berhasil dimasukkan")
    for y in ACADEMIC_YEARS:
        n = len(list(_active_ids(y)))
        print(f"  {y}: {n} siswa aktif")
    print(f"  total: students={len(STUDENT_NAMES)} | grades={len(grade_data)} | "
          f"attendance={len(att_data)} | extracurricular={len(se_data)} | "
          f"homeroom_teachers={len(ht_data)}")


if __name__ == "__main__":
    engine = wait_for_db()
    run_migration(engine)
    seed(engine)
    print("[migrate] Selesai")
