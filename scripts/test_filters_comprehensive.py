"""Comprehensive filter + entity resolution tests."""
import sys
sys.path.insert(0, ".")
from app.intents.loader import get_intent
from app.ai.keyword_classifier import classify_by_keyword
from app.ai.filter_resolver import FilterResolver
from app.services.bp_database_service import BPDatabaseService

resolver = FilterResolver()
svc = BPDatabaseService()

scenarios = [
    # ── BP: KPI card with various filters ──
    ("total izin bp batam", "bp_all_kpi_card", [], ["perizinan", "kategori_status"]),
    ("total izin bp batam tahun 2025", "bp_all_kpi_card", ["tahun"], []),
    ("total izin PB bp batam", "bp_all_kpi_card", ["perizinan"], []),
    ("total izin PL bp batam tahun 2025", "bp_all_kpi_card", ["perizinan", "tahun"], []),
    ("total izin terbit bp batam", "bp_all_kpi_card", ["kategori_status"], []),
    ("total izin tolak bp batam", "bp_all_kpi_card", ["kategori_status"], []),
    ("total izin dalam proses bp batam", "bp_all_kpi_card", ["kategori_status"], []),
    ("total izin PB yang terbit bp batam", "bp_all_kpi_card", ["perizinan", "kategori_status"], []),
    ("total izin LALIN bp batam tahun 2025", "bp_all_kpi_card", ["perizinan", "tahun"], []),
    ("jumlah izin PB bulan januari 2025", "bp_all_kpi_card", ["perizinan", "tahun", "bulan"], []),
    ("total izin bp batam 3 bulan terakhir", "bp_all_kpi_card", ["tgl_status_terakhir"], []),
    ("total izin PB 6 bulan terakhir", "bp_all_kpi_card", ["perizinan", "tgl_status_terakhir"], []),

    # ── BP: Flow with izin filter ──
    ("flow izin PB bp batam", "bp_flow_permohonan", ["pilih_izin"], []),
    ("flow izin PL bp batam tahun 2025", "bp_flow_permohonan", ["pilih_izin", "filter_tahun"], []),

    # ── BP: Tren with izin filter ──
    ("tren inflow PL bp batam", "bp_tren_inflow_outflow", ["pilih_izin"], []),
    ("tren inflow PB tahun 2025", "bp_tren_inflow_outflow", ["pilih_izin", "filter_tahun"], []),

    # ── BP: SLA ──
    ("sla bp batam tahun 2025", "bp_kepatuhan_sla", ["filter_tahun"], []),
    ("kepatuhan SLA PB", "bp_kepatuhan_sla", ["pilih_izin"], []),

    # ── BP: Funnel ──
    ("funnel PB bp batam", "bp_funnel_kemacetan", ["pilih_izin"], []),
    ("kemacetan PL 3 bulan terakhir", "bp_funnel_kemacetan", ["pilih_izin", "rentang_tgl_masuk"], []),

    # ── BP: Gauge ──
    ("gauge performa PB", "bp_gauge_performa", ["pilih_izin"], []),

    # ── BP: Rapor staf ──
    ("rapor staf PB", "bp_rapor_staf", ["pilih_izin"], []),

    # ── BP: Proporsi kerja ──
    ("proporsi kerja PL", "bp_proporsi_kerja", ["pilih_izin"], []),

    # ── OSS ──
    ("kpi oss tahun 2025", "oss_kpi_card", ["filter_tahun"], []),
    ("total oss PB tahun 2025", "oss_kpi_card", ["pilih_izin", "filter_tahun"], []),
    ("sebaran risiko oss PL", "oss_sebaran_risiko", ["pilih_izin"], []),
    ("funnel oss PB", "oss_funnel_kemacetan", ["pilih_izin"], []),

    # ── iBOSS ──
    ("kpi iboss", "iboss_kpi_card", [], []),
    ("total iboss tahun 2025", "iboss_kpi_card", ["pilih_tahun"], []),

    # ── Cross-source: BP should NOT match OSS/iBOSS ──
    ("total izin oss", "oss_kpi_card", [], []),
    ("kpi iboss", "iboss_kpi_card", [], []),
]

print(f"{'Query':<50} {'Intent':<30} {'Filters Set':<40} SQL")
print("="*170)

ok = 0
fail = 0
for query, expected_id, must_have, must_not_have in scenarios:
    result = classify_by_keyword(query)
    if not result:
        print(f"  FAIL: '{query}' -> NO INTENT")
        fail += 1
        continue

    intent_id = result["intent"]
    resolved = resolver.apply(query, intent_id)
    meta = get_intent(intent_id)
    
    payload = {"intent": intent_id, **resolved}
    sql = svc.generate_sql(payload)

    intent_ok = intent_id == expected_id
    has_keys = all(k in resolved for k in must_have)
    no_keys = all(k not in resolved for k in must_not_have)
    sql_ok = bool(sql)

    status = "OK" if (intent_ok and has_keys and no_keys and sql_ok) else "FAIL"
    if status == "OK":
        ok += 1
        print(f"  OK:   '{query:<44}' -> {intent_id:<28} {str(list(resolved.keys())):<40} OK")
    else:
        fail += 1
        details = []
        if not intent_ok: details.append(f"intent={intent_id}(expected {expected_id})")
        if not has_keys: details.append(f"missing {must_have}")
        if not no_keys: details.append(f"extra {[k for k in must_not_have if k in resolved]}")
        if not sql_ok: details.append("no sql")
        print(f"  FAIL: '{query:<44}' -> {intent_id:<28} {str(list(resolved.keys())):<40} {', '.join(details)}")

print("="*170)
print(f"Results: {ok} OK, {fail} FAIL")
