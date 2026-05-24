# EduQuery AI — Intent & Query Reference

> **Catatan:** Daftar intent dikelola secara dinamis melalui file `prompts/intents.json`.
> Admin dapat menambah/mengedit/menghapus intent melalui halaman `/intents` di website.
> Dokumen ini adalah referensi untuk intent bawaan (default).

## Daftar Tabel

| Tabel | Deskripsi |
|-------|-----------|
| `students` | Data siswa (nama, kelas, gender) |
| `teachers` | Data guru (nama, mata pelajaran, gender) |
| `classrooms` | Data ruang kelas (nama kelas, nomor ruang) |
| `subjects` | Daftar mata pelajaran |
| `grades` | Nilai siswa per mata pelajaran per semester |
| `attendance` | Absensi harian siswa (hadir, izin, sakit, alpha) |
| `extracurriculars` | Daftar kegiatan ekstrakurikuler |
| `student_extracurriculars` | Keikutsertaan siswa dalam ekskul |
| `homeroom_teachers` | Wali kelas per tahun ajaran |

---

## Intent Reference (27 Intents)

### 1. `count_students`
- **Deskripsi:** Menghitung jumlah siswa (dapat difilter per kelas)
- **SQL Template:**
  ```sql
  WITH target AS (
      SELECT 1
      FROM students
      WHERE ('{kelas}' = '' OR class = '{kelas}' OR class LIKE '{kelas} %')
  )
  SELECT COUNT(*) AS count
  FROM target
  ```
- **Contoh pertanyaan:**
  - "Berapa jumlah siswa?"
  - "Berapa siswa di kelas X IPA?"

---

### 2. `count_students_by_name`
- **Deskripsi:** Menghitung jumlah siswa yang namanya mengandung kata tertentu
- **SQL Template:**
  ```sql
  WITH filtered AS (
      SELECT 1
      FROM students
      WHERE (name LIKE '%{nama}%'{extra_nama_clause})
  )
  SELECT COUNT(*) AS count
  FROM filtered
  ```
- **Contoh pertanyaan:**
  - "Ada berapa yang namanya Dewi?"
  - "Jumlah siswa bernama Budi"
  - "Ada berapa yang namanya Maya dan Dewi?"

---

### 3. `list_students`
- **Deskripsi:** Daftar siswa (bisa filter per kelas)
- **SQL Template:**
  ```sql
  WITH target AS (
      SELECT *
      FROM students
      WHERE ('{kelas}' = '' OR class = '{kelas}' OR class LIKE '{kelas} %')
  )
  SELECT name, class, gender
  FROM target
  ```
- **Contoh pertanyaan:**
  - "Siapa saja siswa kelas X IPA?"
  - "Tampilkan siswa kelas XI IPS"

---

### 4. `list_students_by_name`
- **Deskripsi:** Mencari siswa berdasarkan nama
- **SQL Template:**
  ```sql
  WITH filtered AS (
      SELECT name, class, gender
      FROM students
      WHERE (name LIKE '%{nama}%'{extra_nama_clause})
  )
  SELECT name, class, gender
  FROM filtered
  ```
- **Contoh pertanyaan:**
  - "Siapa saja yang namanya Dewi?"
  - "Cari siswa bernama Budi"

---

### 5. `count_teachers`
- **Deskripsi:** Menghitung jumlah guru
- **SQL Template:**
  ```sql
  WITH all_teachers AS (
      SELECT 1
      FROM teachers
  )
  SELECT COUNT(*) AS count
  FROM all_teachers
  ```
- **Contoh pertanyaan:**
  - "Berapa jumlah guru?"

---

### 4. `list_teachers`
- **Deskripsi:** Daftar semua guru
- **SQL Template:**
  ```sql
  WITH all_teachers AS (
      SELECT name, subject, gender
      FROM teachers
  )
  SELECT name, subject, gender
  FROM all_teachers
  ```
- **Contoh pertanyaan:**
  - "Daftar guru"
  - "Siapa saja guru?"

---

### 5. `teacher_by_subject`
- **Deskripsi:** Cari guru berdasarkan mata pelajaran
- **SQL Template:**
  ```sql
  WITH subject_teachers AS (
      SELECT name, gender
      FROM teachers
      WHERE subject = '{subject}'
  )
  SELECT name, gender
  FROM subject_teachers
  ```
- **Contoh pertanyaan:**
  - "Guru matematika siapa?"
  - "Siapa guru bahasa Inggris?"

---

### 6. `list_subjects`
- **Deskripsi:** Daftar semua mata pelajaran
- **SQL Template:**
  ```sql
  WITH all_subjects AS (
      SELECT name
      FROM subjects
  )
  SELECT name
  FROM all_subjects
  ```
- **Contoh pertanyaan:**
  - "Apa saja mata pelajaran?"

---

### 7. `list_students_gender`
- **Deskripsi:** Daftar siswa berdasarkan jenis kelamin
- **SQL Template:**
  ```sql
  WITH filtered AS (
      SELECT name, class, gender
      FROM students
      WHERE gender = '{gender}'
  )
  SELECT name, class, gender
  FROM filtered
  ```
- **Contoh pertanyaan:**
  - "Siapa saja siswa laki-laki?"
  - "Daftar siswa perempuan"

---

### 8. `count_students_gender`
- **Deskripsi:** Jumlah siswa berdasarkan jenis kelamin
- **SQL Template:**
  ```sql
  WITH filtered AS (
      SELECT 1
      FROM students
      WHERE gender = '{gender}'
  )
  SELECT COUNT(*) AS count
  FROM filtered
  ```
- **Contoh pertanyaan:**
  - "Berapa jumlah siswa laki-laki?"
  - "Jumlah siswa perempuan"

---

### 9. `student_average_score`
- **Deskripsi:** Rata-rata nilai seorang siswa
- **SQL Template:**
  ```sql
  WITH student_grades AS (
      SELECT g.score
      FROM grades g
      JOIN students s ON s.id = g.student_id
      WHERE s.name LIKE '{name}%'
          AND g.academic_year = '{academic_year}'
          AND g.semester = '{semester}'
  )
  SELECT AVG(score) AS average
  FROM student_grades
  ```
- **Contoh pertanyaan:**
  - "Rata-rata nilai Budi?"
  - "Nilai rata-rata Sari"

---

### 10. `top_students`
- **Deskripsi:** Siswa dengan nilai tertinggi di suatu mata pelajaran
- **SQL Template:**
  ```sql
  WITH ranked AS (
      SELECT
          s.name,
          s.class,
          g.score,
          ROW_NUMBER() OVER (ORDER BY g.score DESC) AS rn
      FROM grades g
      JOIN students s ON s.id = g.student_id
      WHERE g.subject = '{subject}'
          AND g.academic_year = '{academic_year}'
          AND g.semester = '{semester}'
  )
  SELECT name, class, score
  FROM ranked
  WHERE rn <= 5
  ```
- **Contoh pertanyaan:**
  - "Siswa dengan nilai tertinggi di matematika?"
  - "Top 5 siswa fisika"

---

### 11. `class_attendance`
- **Deskripsi:** Jumlah siswa tidak hadir (alpha) di suatu kelas
- **SQL Template:**
  ```sql
  WITH alpha_students AS (
      SELECT 1
      FROM attendance
      WHERE (class = '{kelas}' OR class LIKE '{kelas} %')
          AND status = 'alpha'
  )
  SELECT COUNT(*) AS count
  FROM alpha_students
  ```
- **Contoh pertanyaan:**
  - "Berapa siswa tidak hadir di kelas X IPA?"
  - "Jumlah alpha di kelas X"

---

### 12. `homeroom_teacher`
- **Deskripsi:** Mencari wali kelas
- **SQL Template:**
  ```sql
  WITH teacher_match AS (
      SELECT t.name
      FROM homeroom_teachers ht
      JOIN teachers t ON t.id = ht.teacher_id
      WHERE ht.class = '{kelas}'
          AND ht.academic_year = '{academic_year}'
  )
  SELECT name
  FROM teacher_match
  LIMIT 1
  ```
- **Contoh pertanyaan:**
  - "Siapa wali kelas XI IPA?"

---

### 13. `student_extracurriculars`
- **Deskripsi:** Siswa yang mengikuti ekstrakurikuler tertentu
- **SQL Template:**
  ```sql
  WITH participants AS (
      SELECT s.name, s.class
      FROM student_extracurriculars se
      JOIN students s ON s.id = se.student_id
      JOIN extracurriculars e ON e.id = se.extracurricular_id
      WHERE e.name = '{extracurricular}'
  )
  SELECT name, class
  FROM participants
  ```
- **Contoh pertanyaan:**
  - "Siswa yang ikut pramuka?"
  - "Peserta paskibra"

---

### 14. `count_students_pass`
- **Deskripsi:** Jumlah siswa yang lulus (nilai >= 75) di suatu mata pelajaran
- **SQL Template:**
  ```sql
  WITH passed AS (
      SELECT 1
      FROM grades
      WHERE subject = '{subject}'
          AND score >= 75
  )
  SELECT COUNT(*) AS count
  FROM passed
  ```
- **Contoh pertanyaan:**
  - "Berapa siswa lulus matematika?"

---

### 15. `list_teachers_gender`
- **Deskripsi:** Daftar guru berdasarkan jenis kelamin
- **SQL Template:**
  ```sql
  WITH filtered AS (
      SELECT name, subject, gender
      FROM teachers
      WHERE gender = '{gender}'
  )
  SELECT name, subject, gender
  FROM filtered
  ```
- **Contoh pertanyaan:**
  - "Siapa guru laki-laki?"
  - "Daftar guru perempuan"

---

### 16. `count_students_gender_per_class`
- **Deskripsi:** Jumlah siswa per kelas berdasarkan jenis kelamin
- **SQL Template:**
  ```sql
  WITH grouped AS (
      SELECT
          class,
          gender,
          COUNT(*) AS cnt
      FROM students
      GROUP BY class, gender
  )
  SELECT class, gender, cnt AS count
  FROM grouped
  ORDER BY class, gender
  ```
- **Contoh pertanyaan:**
  - "Jumlah siswa per kelas berdasarkan jenis kelamin"
  - "Berapa siswa laki-laki dan perempuan tiap kelas"

---

### 17. `count_students_per_class_per_year`
- **Deskripsi:** Jumlah siswa per kelas menurut tahun ajaran
- **SQL Template:**
  ```sql
  WITH yearly AS (
      SELECT
          g.class,
          g.academic_year,
          COUNT(DISTINCT g.student_id) AS cnt
      FROM grades g
      GROUP BY g.class, g.academic_year
  )
  SELECT class, academic_year, cnt AS count
  FROM yearly
  ORDER BY class, academic_year
  ```
- **Contoh pertanyaan:**
  - "Jumlah siswa per kelas menurut tahun ajaran"
  - "Berapa siswa tiap kelas setiap tahun"

---

### 18. `average_score_per_class_by_subject`
- **Deskripsi:** Rata-rata nilai mata pelajaran tertentu per kelas di suatu tahun ajaran
- **SQL Template:**
  ```sql
  WITH subject_grades AS (
      SELECT s.class, g.score
      FROM grades g
      JOIN students s ON s.id = g.student_id
      WHERE g.subject = '{subject}'
          AND g.academic_year = '{academic_year}'
  )
  SELECT class, AVG(score) AS average
  FROM subject_grades
  GROUP BY class
  ORDER BY class
  ```
- **Contoh pertanyaan:**
  - "Rata-rata nilai matematika tiap kelas di tahun ajaran 2024/2025"
  - "Nilai rata-rata fisika per kelas"

---

### 19. `lowest_average_per_class`
- **Deskripsi:** Siswa dengan nilai rata-rata terendah per kelas di tahun ajaran tertentu
- **SQL Template:**
  ```sql
  WITH student_avg AS (
      SELECT
          s.class,
          s.name,
          AVG(g.score) AS average
      FROM grades g
      JOIN students s ON s.id = g.student_id
      WHERE g.academic_year = '{academic_year}'
          AND ('{subject}' = '' OR g.subject = '{subject}')
      GROUP BY s.class, s.name
  ),
  min_avg AS (
      SELECT
          class,
          MIN(average) AS min_average
      FROM student_avg
      GROUP BY class
  )
  SELECT
      sa.class,
      sa.name,
      sa.average
  FROM student_avg sa
  JOIN min_avg ma
      ON sa.class = ma.class
      AND sa.average = ma.min_average
  ORDER BY sa.class
  ```
- **Contoh pertanyaan:**
  - "Siapa yang memiliki nilai rata-rata terendah di tahun ajaran terakhir per kelas"
  - "Siswa dengan rata-rata terendah tiap kelas"

---

### 20. `class_average_score`
- **Deskripsi:** Rata-rata nilai seluruh siswa di suatu kelas
- **SQL Template:**
  ```sql
  WITH class_grades AS (
      SELECT s.name, s.class, g.score
      FROM grades g
      JOIN students s ON s.id = g.student_id
      WHERE (s.class = '{kelas}' OR s.class LIKE '{kelas} %')
  )
  SELECT name, class, AVG(score) AS average
  FROM class_grades
  GROUP BY name, class
  ORDER BY name
  ```
- **Contoh pertanyaan:**
  - "Berapa rata-rata kelas X IPA?"
  - "Rata-rata nilai kelas 10"

---

### 21. `count_teachers_gender`
- **Deskripsi:** Jumlah guru berdasarkan jenis kelamin
- **SQL Template:**
  ```sql
  WITH filtered AS (
      SELECT 1
      FROM teachers
      WHERE gender = '{gender}'
  )
  SELECT COUNT(*) AS count
  FROM filtered
  ```
- **Contoh pertanyaan:**
  - "Berapa jumlah guru laki-laki?"
  - "Jumlah guru perempuan"

---

### 22. `list_extracurriculars`
- **Deskripsi:** Daftar semua ekstrakurikuler beserta pelatihnya
- **SQL Template:**
  ```sql
  WITH all_ec AS (
      SELECT name, coach
      FROM extracurriculars
  )
  SELECT name, coach
  FROM all_ec
  ORDER BY name
  ```
- **Contoh pertanyaan:**
  - "Apa saja ekstrakurikuler?"
  - "Daftar ekskul dan pelatihnya"

---

### 23. `list_classes`
- **Deskripsi:** Daftar semua kelas beserta nomor ruangannya
- **SQL Template:**
  ```sql
  WITH all_classes AS (
      SELECT class, room_number
      FROM classrooms
  )
  SELECT class, room_number
  FROM all_classes
  ORDER BY class
  ```
- **Contoh pertanyaan:**
  - "Apa saja kelas yang ada?"
  - "Daftar kelas dan ruangannya"

---

### 24. `attendance_by_status`
- **Deskripsi:** Jumlah siswa berdasarkan status kehadiran di suatu kelas
- **SQL Template:**
  ```sql
  WITH status_count AS (
      SELECT 1
      FROM attendance
      WHERE (class = '{kelas}' OR class LIKE '{kelas} %')
          AND status = '{status}'
  )
  SELECT COUNT(*) AS count
  FROM status_count
  ```
- **Contoh pertanyaan:**
  - "Berapa siswa sakit di kelas X IPA?"
  - "Jumlah siswa izin di kelas XI IPS"

---

### 25. `extracurricular_by_coach`
- **Deskripsi:** Cari ekstrakurikuler berdasarkan nama pelatih
- **SQL Template:**
  ```sql
  WITH coach_ec AS (
      SELECT name, coach
      FROM extracurriculars
      WHERE coach = '{coach}'
  )
  SELECT name, coach
  FROM coach_ec
  ```
- **Contoh pertanyaan:**
  - "Ekstrakurikuler yang dibina Agus Wijaya?"
  - "Ekskul dengan pelatih Rudi Hartono"

---

### 26. `attendance_detail`
- **Deskripsi:** Daftar kehadiran siswa di suatu kelas pada tanggal tertentu
- **SQL Template:**
  ```sql
  WITH att AS (
      SELECT s.name, a.status
      FROM attendance a
      JOIN students s ON s.id = a.student_id
      WHERE (a.class = '{kelas}' OR a.class LIKE '{kelas} %')
          AND a.attendance_date = '{tanggal}'
  )
  SELECT name, status
  FROM att
  ORDER BY name
  ```
- **Contoh pertanyaan:**
  - "Siapa saja yang hadir di kelas X IPA tanggal 2024-01-10?"
  - "Kehadiran siswa kelas XI IPS pada 2024-02-10"

---

### 27. `top_students_overall`
- **Deskripsi:** Siswa dengan rata-rata nilai tertinggi di semua mata pelajaran
- **SQL Template:**
  ```sql
  WITH ranked AS (
      SELECT
          s.name,
          s.class,
          AVG(g.score) AS average,
          ROW_NUMBER() OVER (ORDER BY AVG(g.score) DESC) AS rn
      FROM grades g
      JOIN students s ON s.id = g.student_id
      WHERE g.academic_year = '{academic_year}'
          AND g.semester = '{semester}'
      GROUP BY s.name, s.class
  )
  SELECT name, class, ROUND(average, 2) AS average
  FROM ranked
  WHERE rn <= 5
  ```
- **Contoh pertanyaan:**
  - "Siapa siswa dengan rata-rata tertinggi semester ini?"
  - "Top 5 siswa terbaik tahun ajaran 2024/2025"

---

## Matrix Tabel vs Intent

| Intent | students | teachers | subjects | grades | attendance | extracurriculars | homeroom_teachers | classrooms |
|--------|----------|----------|----------|--------|------------|-----------------|-------------------|------------|
| count_students | ✅ | | | | | | | |
| list_students | ✅ | | | | | | | |
| count_teachers | | ✅ | | | | | | |
| list_teachers | | ✅ | | | | | | |
| teacher_by_subject | | ✅ | | | | | | |
| list_subjects | | | ✅ | | | | | |
| list_students_gender | ✅ | | | | | | | |
| count_students_gender | ✅ | | | | | | | |
| student_average_score | ✅ | | | ✅ | | | | |
| top_students | ✅ | | | ✅ | | | | |
| class_attendance | | | | | ✅ | | | |
| homeroom_teacher | | ✅ | | | | | ✅ | |
| student_extracurriculars | ✅ | | | | | ✅ | | |
| count_students_pass | | | | ✅ | | | | |
| list_teachers_gender | | ✅ | | | | | | |
| count_students_gender_per_class | ✅ | | | | | | | |
| count_students_per_class_per_year | ✅ | | | ✅ | | | | |
| average_score_per_class_by_subject | ✅ | | | ✅ | | | | |
| lowest_average_per_class | ✅ | | | ✅ | | | | |
| class_average_score | ✅ | | | ✅ | | | | |
| count_teachers_gender | | ✅ | | | | | | |
| list_extracurriculars | | | | | | ✅ | | |
| list_classes | | | | | | | | ✅ |
| attendance_by_status | | | | | ✅ | | | |
| extracurricular_by_coach | | | | | | ✅ | | |
| attendance_detail | ✅ | | | | ✅ | | | |
| top_students_overall | ✅ | | | ✅ | | | | |
