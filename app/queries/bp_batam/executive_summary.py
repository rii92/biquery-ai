"""Executive Summary — seluruh query untuk sub-menu Executive Summary BP Batam.

Setiap query menggunakan placeholder {{param}} yang akan di-replace
dengan nilai filter saat eksekusi.
"""

_PERMIT_TYPES = "'PB', 'PBUMKU', 'PL', 'PKKPRL', 'PPKH'"

_QUERY_RAW = {
    "total_masuk": {
        "label": "Total Masuk",
        "sql": """\
SELECT
    CAST(TRUNC(TGL_STATUS_TERAKHIR, 'IW') AS TIMESTAMP) AS PERIODE,
    COUNT(*)                                             AS TOTAL_MASUK
FROM US_DWH.BI_MART_STATUS_PERIZINAN
WHERE PERIZINAN IN ('PL', 'PB', 'PBUMKU', 'PKKPRL', 'PB')
  AND {{tgl_status_terakhir}}
  AND {{perizinan}}
GROUP BY TRUNC(TGL_STATUS_TERAKHIR, 'IW')
ORDER BY TRUNC(TGL_STATUS_TERAKHIR, 'IW') ASC""",
        "params": {
            "tgl_status_terakhir": "Filter tanggal (contoh: TGL_STATUS_TERAKHIR >= TO_DATE('2024-01-01','YYYY-MM-DD'))",
            "perizinan": "Filter jenis izin (contoh: PERIZINAN IN ('PB','PL'))",
        },
    },
    "izin_terbit_per_bulan": {
        "label": "Izin Terbit per Bulan",
        "sql": """\
SELECT
    CAST(TRUNC(TGL_STATUS_TERAKHIR, 'IW') AS TIMESTAMP) AS PERIODE,
    COUNT(*)                                             AS IZIN_TERBIT
FROM US_DWH.BI_MART_STATUS_PERIZINAN
WHERE KATEGORI_STATUS = 'Terbit'
  AND PERIZINAN IN ({{PERMIT_TYPES}})
  AND {{tgl_status_terakhir}}
  AND {{perizinan}}
GROUP BY TRUNC(TGL_STATUS_TERAKHIR, 'IW')
ORDER BY TRUNC(TGL_STATUS_TERAKHIR, 'IW') ASC""",
        "params": {
            "tgl_status_terakhir": "Filter tanggal",
            "perizinan": "Filter jenis izin",
        },
    },
    "total_backlog_per_bulan": {
        "label": "Total Backlog per Bulan",
        "sql": """\
SELECT
    CAST(TRUNC(TGL_STATUS_TERAKHIR, 'IW') AS TIMESTAMP) AS PERIODE,
    COUNT(*)                                             AS TOTAL_BACKLOG
FROM US_DWH.BI_MART_STATUS_PERIZINAN
WHERE KATEGORI_STATUS NOT IN ('Terbit')
  AND KATEGORI_STATUS NOT LIKE '%Ditolak%'
  AND KATEGORI_STATUS NOT LIKE '%Batal%'
  AND PERIZINAN IN ({{PERMIT_TYPES}})
  AND {{tgl_status_terakhir}}
  AND {{perizinan}}
GROUP BY TRUNC(TGL_STATUS_TERAKHIR, 'IW')
ORDER BY TRUNC(TGL_STATUS_TERAKHIR, 'IW') ASC""",
        "params": {
            "tgl_status_terakhir": "Filter tanggal",
            "perizinan": "Filter jenis izin",
        },
    },
    "dalam_proses": {
        "label": "Dalam Proses",
        "sql": """\
SELECT
    TRUNC(TGL_STATUS_TERAKHIR, 'DD') AS TANGGAL,
    COUNT(*)                          AS JUMLAH_PERMOHONAN
FROM US_DWH.BI_MART_STATUS_PERIZINAN
WHERE UPPER(KATEGORI_STATUS) LIKE '%DALAM PROSES%'
  AND TGL_STATUS_TERAKHIR IS NOT NULL
  AND PERIZINAN IN ({{PERMIT_TYPES}})
  AND {{tgl_status_terakhir}}
  AND {{perizinan}}
GROUP BY TRUNC(TGL_STATUS_TERAKHIR, 'DD')
ORDER BY TRUNC(TGL_STATUS_TERAKHIR, 'DD') ASC""",
        "params": {
            "tgl_status_terakhir": "Filter tanggal",
            "perizinan": "Filter jenis izin",
        },
    },
    "sebaran_berdasarkan_jenis_izin": {
        "label": "Sebaran Berdasarkan Jenis Izin",
        "sql": """\
SELECT
    CASE PERIZINAN
        WHEN 'PBUMKU' THEN 'PBUMKU'
        WHEN 'PB'     THEN 'PB'
        WHEN 'PL'     THEN 'PL'
        WHEN 'PKKPRL' THEN 'PKKPRL'
        WHEN 'PPKH'   THEN 'PPKH'
        ELSE PERIZINAN
    END AS JENIS_IZIN,
    CASE
        WHEN KATEGORI_STATUS = 'Terbit'                       THEN 'Terbit'
        WHEN KATEGORI_STATUS LIKE '%Tolak%'
          OR KATEGORI_STATUS LIKE '%Ditolak%'
          OR KATEGORI_STATUS LIKE '%Rejected%'                THEN 'Tolak'
        ELSE 'Proses'
    END AS KELOMPOK_STATUS,
    COUNT(*) AS JUMLAH
FROM US_DWH.BI_MART_STATUS_PERIZINAN
WHERE 1 = 1
  AND PERIZINAN IN ({{PERMIT_TYPES}})
  AND {{kategori_status}}
  AND {{perizinan}}
  AND {{tgl_status_terakhir}}
GROUP BY
    PERIZINAN,
    CASE
        WHEN KATEGORI_STATUS = 'Terbit'                       THEN 'Terbit'
        WHEN KATEGORI_STATUS LIKE '%Tolak%'
          OR KATEGORI_STATUS LIKE '%Ditolak%'
          OR KATEGORI_STATUS LIKE '%Rejected%'                THEN 'Tolak'
        ELSE 'Proses'
    END
ORDER BY JUMLAH DESC""",
        "params": {
            "kategori_status": "Filter kategori status (contoh: KATEGORI_STATUS = 'Terbit')",
            "perizinan": "Filter jenis izin",
            "tgl_status_terakhir": "Filter tanggal",
        },
    },
    "komposisi_keseluruhan_status": {
        "label": "Komposisi Keseluruhan Status",
        "sql": """\
SELECT
    CAST(TRUNC(TGL_STATUS_TERAKHIR, 'IW') AS TIMESTAMP) AS PERIODE,
    CASE
        WHEN KATEGORI_STATUS = 'Terbit'                       THEN 'Terbit'
        WHEN KATEGORI_STATUS LIKE '%Tolak%'
          OR KATEGORI_STATUS LIKE '%Ditolak%'
          OR KATEGORI_STATUS LIKE '%Rejected%'                THEN 'Ditolak'
        ELSE 'Dalam Proses'
    END AS KELOMPOK_STATUS,
    COUNT(*) AS JUMLAH
FROM US_DWH.BI_MART_STATUS_PERIZINAN
WHERE {{tgl_status_terakhir}}
  AND PERIZINAN IN ({{PERMIT_TYPES}})
  AND {{perizinan}}
  AND {{kategori_status}}
GROUP BY
    TRUNC(TGL_STATUS_TERAKHIR, 'IW'),
    CASE
        WHEN KATEGORI_STATUS = 'Terbit'                       THEN 'Terbit'
        WHEN KATEGORI_STATUS LIKE '%Tolak%'
          OR KATEGORI_STATUS LIKE '%Ditolak%'
          OR KATEGORI_STATUS LIKE '%Rejected%'                THEN 'Ditolak'
        ELSE 'Dalam Proses'
    END
ORDER BY TRUNC(TGL_STATUS_TERAKHIR, 'IW') ASC, JUMLAH DESC""",
        "params": {
            "tgl_status_terakhir": "Filter tanggal",
            "perizinan": "Filter jenis izin",
            "kategori_status": "Filter kategori status",
        },
    },
}


def _build_queries() -> dict:
    out = {}
    for qid, meta in _QUERY_RAW.items():
        sql = meta["sql"].replace("{{PERMIT_TYPES}}", _PERMIT_TYPES)
        out[qid] = {"label": meta["label"], "sql": sql, "params": dict(meta["params"])}
    return out


QUERIES = _build_queries()


def get_query(query_id: str) -> dict | None:
    return QUERIES.get(query_id)


def list_queries() -> list[dict]:
    return [
        {"id": qid, "label": meta["label"], "params": list(meta["params"].keys())}
        for qid, meta in QUERIES.items()
    ]
