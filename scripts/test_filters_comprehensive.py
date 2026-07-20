"""Comprehensive filter testing for all scenarios."""
import sys
sys.path.insert(0, ".")
from app.intents.loader import find_intent_by_keywords, get_intent
from app.ai.filter_resolver import FilterResolver
from app.services.bp_database_service import BPDatabaseService

resolver = FilterResolver()
svc = BPDatabaseService()

scenarios = [
    # (query, expected_intent_desc, check_filter_keys, check_no_filter_keys)
    
    # BP scenarios
    ("total izin bp batam", "bp_all_kpi_card", [], ["tahun", "bulan", "tgl_status_terakhir"]),
    ("total izin bp batam tahun 2025", "bp_all_kpi_card", ["tahun"], []),
    ("total izin bp batam tahun 2025 bulan januari", "bp_all_kpi_card", ["tahun", "bulan"], []),
    ("total izin bp batam 3 bulan terakhir", "bp_all_kpi_card", ["tgl_status_terakhir"], []),
    ("jumlah izin bp batam tahun ini", "bp_all_kpi_card", ["tahun"], []),
    ("total permohonan bp batam", "bp_all_kpi_card", [], []),
    ("kpi bp batam", "bp_all_kpi_card", [], []),
    ("ringkasan permohonan bp batam", "bp_all_kpi_card", [], []),
    
    # Flow / Sankey
    ("flow permohonan bp batam", "bp_flow_permohonan", [], []),
    ("flow bp batam tahun 2025", "bp_flow_permohonan", ["filter_tahun"], []),
    ("flow bp batam 6 bulan terakhir", "bp_flow_permohonan", ["rentang_tgl_masuk"], []),
    
    # Tren
    ("tren inflow outflow bp batam", "bp_tren_inflow_outflow", [], []),
    ("tren inflow bp batam tahun 2025", "bp_tren_inflow_outflow", ["filter_tahun"], []),
    
    # Gauge
    ("gauge performa bp batam", "bp_gauge_performa", [], []),
    ("tingkat penyelesaian bp batam tahun 2025", "bp_gauge_performa", ["filter_tahun"], []),
    
    # SLA
    ("sla bp batam", "bp_kepatuhan_sla", [], []),
    ("kepatuhan sla bp batam tahun 2025", "bp_kepatuhan_sla", ["filter_tahun"], []),
    
    # Funnel
    ("funnel bp batam", "bp_funnel_kemacetan", [], []),
    ("kemacetan bp batam 3 bulan terakhir", "bp_funnel_kemacetan", ["rentang_tgl_masuk"], []),
    
    # Proporsi kerja
    ("proporsi kerja bp batam", "bp_proporsi_kerja", [], []),
    ("jam kerja bp batam tahun 2025", "bp_proporsi_kerja", ["filter_tahun"], []),
    
    # Rapor staf
    ("rapor staf bp batam", "bp_rapor_staf", [], []),
    ("evaluasi staf bp batam tahun 2025", "bp_rapor_staf", ["filter_tahun"], []),

    # OSS scenarios
    ("kpi oss", "oss_kpi_card", [], []),
    ("total oss tahun 2025", "oss_kpi_card", ["filter_tahun"], []),
    ("performa oss tahun ini", "oss_gauge_performa", ["filter_tahun"], []),
    ("sebaran risiko oss 6 bulan terakhir", "oss_sebaran_risiko", ["rentang_tgl_masuk"], []),
    ("funnel oss tahun 2025", "oss_funnel_kemacetan", ["filter_tahun"], []),
    ("sla oss", "oss_kepatuhan_sla", [], []),
    ("detail oss", "oss_detail_permohonan", [], []),

    # iBOSS scenarios
    ("kpi iboss", "iboss_kpi_card", [], []),
    ("total iboss tahun 2025", "iboss_kpi_card", ["pilih_tahun"], []),
    ("overdue iboss", "iboss_overdue", [], []),
    ("gauge iboss", "iboss_gauge_performa", [], []),
    ("sebaran iboss", "iboss_sebaran_status", [], []),
    ("flow iboss", "iboss_sebaran_proses", [], []),
    ("tren iboss tahun 2025", "iboss_tren_inflow_outflow", ["pilih_tahun"], []),
    ("funnel iboss 3 bulan terakhir", "iboss_funnel_kemacetan", ["rentang_waktu"], []),
    ("rata waktu role iboss", "iboss_rata_waktu_role", [], []),
    ("sla iboss tahun 2025", "iboss_kepatuhan_sla", ["pilih_tahun"], []),
    ("leaderboard iboss", "iboss_leaderboard_sla", [], []),
    ("sebaran overdue iboss", "iboss_sebaran_overdue", [], []),
    ("total overdue iboss tahun 2025", "iboss_total_overdue", ["pilih_tahun"], []),
    ("jam kerja iboss 3 bulan terakhir", "iboss_proporsi_kerja", ["rentang_waktu"], []),
    ("rapor staf iboss", "iboss_rapor_staf", [], []),
    ("detail iboss", "iboss_detail_permohonan", [], []),

    # Edge: BP should NOT match OSS/iBOSS queries
    ("total izin oss", "oss_kpi_card", [], []),
    ("kpi iboss", "iboss_kpi_card", [], []),
]

print(f"{'Query':<50} {'Intent':<30} {'Filters':<50} {'SQL':<8}")
print("="*138)

all_ok = True
for query, expected_intent_desc, check_keys, no_check_keys in scenarios:
    # Step 1: Intent matching
    result = find_intent_by_keywords(query)
    if not result:
        print(f"  FAIL: '{query}' -> NO INTENT MATCHED (expected {expected_intent_desc})")
        all_ok = False
        continue
    
    intent_id = result["intent"]
    
    # Step 2: Filter resolution
    resolved = resolver.apply(query, intent_id)
    
    # Step 3: SQL generation
    meta = get_intent(intent_id)
    payload = {"intent": intent_id, **resolved}
    sql = svc.generate_sql(payload)
    
    # Validate expected intent
    intent_ok = intent_id == expected_intent_desc
    if not intent_ok:
        print(f"  WARN: '{query:<44}' -> {intent_id:<30} {str(list(resolved.keys())):<50} {'OK' if sql else 'FAIL'}")
    
    # Check required filter keys present
    filters_ok = all(k in resolved for k in check_keys)
    no_filters_ok = all(k not in resolved for k in no_check_keys)
    filters_status = "OK" if filters_ok and no_filters_ok else "FILTER_FAIL"
    
    # Check SQL generated
    sql_ok = bool(sql)
    sql_status = "OK" if sql_ok else "NO_SQL"
    
    if intent_ok and filters_ok and no_filters_ok and sql_ok:
        print(f"  OK:   '{query:<44}' -> {intent_id:<30} {str(list(resolved.keys())):<50} OK")
    elif not intent_ok:
        print(f"  WARN: '{query:<44}' -> {intent_id:<30} (expected {expected_intent_desc})")
        all_ok = False
    elif not sql_ok:
        print(f"  FAIL: '{query:<44}' -> {intent_id:<30} {str(list(resolved.keys())):<50} NO SQL!")
        all_ok = False
    else:
        print(f"  FAIL: '{query:<44}' -> {intent_id:<30} {str(list(resolved.keys())):<50} FILTER MISSING: need {check_keys}, avoid {no_check_keys}")
        all_ok = False

print("="*138)
if all_ok:
    print("ALL SCENARIOS PASSED")
else:
    print("SOME SCENARIOS FAILED - see above")
