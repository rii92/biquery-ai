"""Script to add filter_mappings to all intents in intents.json."""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

INTENTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "intents.json")


def filter_mappings_for(intent_id, source, params):
    if source == "bp":
        if intent_id == "bp_all_kpi_card":
            return {
                "tahun": {"param": "tahun", "sql": "TO_CHAR(TGL_STATUS_TERAKHIR, 'YYYY') = '{value}'"},
                "bulan": {"param": "bulan", "sql": "TO_CHAR(TGL_STATUS_TERAKHIR, 'MM') = '{value}'"},
                "tanggal_awal": {"param": "tgl_status_terakhir", "sql": "TRUNC(TGL_STATUS_TERAKHIR) >= TO_DATE('{value}','YYYY-MM-DD')"},
                "tanggal_akhir": {"param": "tgl_status_terakhir", "sql": "TRUNC(TGL_STATUS_TERAKHIR) <= TO_DATE('{value}','YYYY-MM-DD')"},
                "perizinan": {"param": "perizinan", "sql": "UPPER(JENIS_IZIN) = UPPER('{value}')"},
                "kategori_status": {"param": "kategori_status", "sql": "KATEGORI_STATUS = '{value}'"},
            }
        else:
            return {
                "tahun": {"param": "filter_tahun", "sql": "TAHUN = '{value}'"},
                "bulan": {"param": "filter_bulan", "sql": "BULAN = '{value}'"},
                "tanggal_awal": {"param": "rentang_tgl_masuk", "sql": "TGL_MASUK >= TO_DATE('{value}','YYYY-MM-DD')"},
                "tanggal_akhir": {"param": "rentang_tgl_masuk", "sql": "TGL_MASUK <= TO_DATE('{value}','YYYY-MM-DD')"},
                "perizinan": {"param": "pilih_izin", "sql": "(UPPER(JENIS_IZIN) = UPPER('{value}') OR UPPER(KATEGORI_IZIN_LALIN) = UPPER('{value}'))"},
                "kategori_status": {"param": "kategori_status", "sql": "KATEGORI_STATUS = '{value}'"},
            }
    elif source == "oss":
        return {
            "tahun": {"param": "filter_tahun", "sql": "TAHUN = '{value}'"},
            "bulan": {"param": "filter_bulan", "sql": "BULAN = '{value}'"},
            "tanggal_awal": {"param": "rentang_tgl_masuk", "sql": "TGL_MASUK >= TO_DATE('{value}','YYYY-MM-DD')"},
            "tanggal_akhir": {"param": "rentang_tgl_masuk", "sql": "TGL_MASUK <= TO_DATE('{value}','YYYY-MM-DD')"},
            "perizinan": {"param": "pilih_izin", "sql": "UPPER(JENIS_IZIN) = UPPER('{value}')"},
            "kategori_status": {"param": "kategori_status", "sql": "KATEGORI_STATUS = '{value}'"},
        }
    elif source == "iboss":
        if intent_id == "iboss_rata_waktu_role":
            return {
                "tahun": {"param": "pilih_tahun", "sql": "TO_CHAR(T_LOG_LICENSING.ACTION_TIME, 'YYYY') = '{value}'"},
                "bulan": {"param": "pilih_bulan", "sql": "TO_CHAR(T_LOG_LICENSING.ACTION_TIME, 'FMMM') = '{value}'"},
                "tanggal_awal": {"param": "rentang_waktu", "sql": "T_LOG_LICENSING.ACTION_TIME >= TO_DATE('{value}','YYYY-MM-DD')"},
                "tanggal_akhir": {"param": "rentang_waktu", "sql": "T_LOG_LICENSING.ACTION_TIME <= TO_DATE('{value}','YYYY-MM-DD')"},
                "perizinan": {"param": "pilih_izin_iboss", "sql": "UPPER(TX_PERMOHONAN.KATEGORI_IZIN) = UPPER('{value}')"},
                "kategori_status": {"param": "kategori_status", "sql": "KATEGORI_STATUS = '{value}'"},
            }
        else:
            return {
                "tahun": {"param": "pilih_tahun", "sql": "TO_CHAR(TX_PERMOHONAN.TGL_DAFTAR, 'YYYY') = '{value}'"},
                "bulan": {"param": "pilih_bulan", "sql": "TO_CHAR(TX_PERMOHONAN.TGL_DAFTAR, 'FMMM') = '{value}'"},
                "tanggal_awal": {"param": "rentang_waktu", "sql": "TX_PERMOHONAN.TGL_DAFTAR >= TO_DATE('{value}','YYYY-MM-DD')"},
                "tanggal_akhir": {"param": "rentang_waktu", "sql": "TX_PERMOHONAN.TGL_DAFTAR <= TO_DATE('{value}','YYYY-MM-DD')"},
                "perizinan": {"param": "pilih_izin_iboss", "sql": "UPPER(TX_PERMOHONAN.KATEGORI_IZIN) = UPPER('{value}')"},
                "kategori_status": {"param": "kategori_status", "sql": "KATEGORI_STATUS = '{value}'"},
            }
    return {}


def main():
    with open(INTENTS_PATH, "r", encoding="utf-8") as f:
        intents = json.load(f)

    modified = 0
    for intent in intents:
        src = intent.get("source", "")
        iid = intent["id"]
        params = intent.get("params", {})
        fm = filter_mappings_for(iid, src, params)
        if fm:
            intent["filter_mappings"] = fm
            modified += 1
            print(f"  added filter_mappings to {iid} ({len(fm)} keys)")

    with open(INTENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(intents, f, indent=2, ensure_ascii=False)

    print(f"\nDone. Modified {modified} intents.")


if __name__ == "__main__":
    main()
