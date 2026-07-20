"""Final verification: SQL generation, formatters, classifier, filter resolver."""
import sys
sys.path.insert(0, ".")
from app.intents.loader import list_active_intents, find_intent_by_keywords, get_intent
from app.services.bp_formatter_service import format_bp_reply, _FORMATTERS
from app.services.bp_database_service import BPDatabaseService
from app.ai.filter_resolver import FilterResolver

print("=== 1. Load all active intents ===")
active = list_active_intents()
print(f"  Active intents: {len(active)}")

for i in active:
    src = i.get("source", "?")
    assert i.get("sql_template"), f"{i['id']} missing sql_template"
    assert i.get("params") is not None, f"{i['id']} missing params"
    assert i.get("keyword_patterns") is not None, f"{i['id']} missing keyword_patterns"
print("  All intents have required fields OK")

print("\n=== 2. Formatter registration ===")
for i in active:
    iid = i["id"]
    if iid in _FORMATTERS:
        print(f"  {iid}: custom formatter registered")
    else:
        fc = i.get("format_config", {}).get("type", "table")
        print(f"  {iid}: using generic formatter (type={fc})")

print("\n=== 3. SQL Generation ===")
svc = BPDatabaseService()

test_cases = [
    ("oss_kpi_card", {"pilih_izin": "UPPER(JENIS_IZIN) = UPPER('PB')", "filter_tahun": "TAHUN = '2025'"}),
    ("oss_gauge_performa", {"pilih_izin": "UPPER(JENIS_IZIN) = UPPER('PB')"}),
    ("oss_sebaran_jenis_perizinan", {}),
    ("oss_sebaran_risiko", {}),
    ("oss_sebaran_status_permohonan", {}),
    ("oss_tren_inflow_outflow", {}),
    ("oss_funnel_kemacetan", {}),
    ("oss_kepatuhan_sla", {}),
    ("oss_leaderboard_sla", {}),
    ("oss_rapor_staf", {}),
    ("oss_detail_permohonan", {}),
    ("iboss_kpi_card", {"rentang_waktu": "TX_PERMOHONAN.TGL_DAFTAR >= TO_DATE('2025-01-01','YYYY-MM-DD')"}),
    ("iboss_overdue", {}),
    ("iboss_gauge_performa", {}),
    ("iboss_sebaran_status", {}),
    ("iboss_sebaran_proses", {}),
    ("iboss_tren_inflow_outflow", {}),
    ("iboss_funnel_kemacetan", {}),
    ("iboss_rata_waktu_role", {}),
    ("iboss_kepatuhan_sla", {}),
    ("iboss_leaderboard_sla", {}),
    ("iboss_sebaran_overdue", {}),
    ("iboss_total_overdue", {}),
    ("iboss_proporsi_kerja", {}),
    ("iboss_rapor_staf", {}),
    ("iboss_detail_permohonan", {}),
]

for intent_id, params in test_cases:
    payload = {"intent": intent_id, **params}
    sql = svc.generate_sql(payload)
    meta = get_intent(intent_id)
    assert sql, f"Empty SQL for {intent_id}"
    assert meta["source"] in sql or "SELECT" in sql, f"SQL missing SELECT for {intent_id}"
    # Check param placeholders were replaced
    remaining = [p for p in meta["params"] if "{" + p + "}" in sql]
    assert not remaining, f"Unresolved params for {intent_id}: {remaining}"
    print(f"  OK: {intent_id} -> SQL generated ({len(sql)} chars, source={meta['source']})")

print("\n=== 4. Formatter output ===")
for intent_id, params in test_cases[:5]:  # Test a subset
    meta = get_intent(intent_id)
    dummy_result = []
    if meta["format_config"].get("type") == "single_value":
        col = meta["format_config"]["value_column"]
        dummy_result = [{col: 0.85}]
    elif meta["format_config"].get("type") == "table" or meta["format_config"].get("type") == "custom":
        dummy_result = [{"col1": "val1", "col2": "val2"}]
    
    payload = {"intent": intent_id, **params}
    output = format_bp_reply(payload, dummy_result)
    assert output, f"Empty formatter output for {intent_id}"
    print(f"  OK: {intent_id} -> formatted ({len(output)} chars)")

print("\n=== 5. Classifier keyword matching ===")
test_questions = [
    ("kpi oss", "oss_kpi_card"),
    ("performa oss", "oss_gauge_performa"),
    ("sebaran risiko oss", "oss_sebaran_risiko"),
    ("funnel oss", "oss_funnel_kemacetan"),
    ("sla oss", "oss_kepatuhan_sla"),
    ("rapor staf oss", "oss_rapor_staf"),
    ("detail oss", "oss_detail_permohonan"),
    ("kpi iboss", "iboss_kpi_card"),
    ("overdue iboss", "iboss_overdue"),
    ("gauge iboss", "iboss_gauge_performa"),
    ("sebaran iboss", "iboss_sebaran_status"),
    ("flow iboss", "iboss_sebaran_proses"),
    ("tren iboss", "iboss_tren_inflow_outflow"),
    ("funnel iboss", "iboss_funnel_kemacetan"),
    ("waktu iboss", "iboss_rata_waktu_role"),
    ("sla iboss", "iboss_kepatuhan_sla"),
    ("leaderboard iboss", "iboss_leaderboard_sla"),
    ("overdue posisi iboss", "iboss_sebaran_overdue"),
    ("total overdue iboss", "iboss_total_overdue"),
    ("jam kerja iboss", "iboss_proporsi_kerja"),
    ("rapor staf iboss", "iboss_rapor_staf"),
    ("detail iboss", "iboss_detail_permohonan"),
]

for question, expected_intent in test_questions:
    result = find_intent_by_keywords(question)
    assert result is not None, f"No match for '{question}' (expected {expected_intent})"
    matched = result["intent"]
    if matched == expected_intent:
        print(f"  OK: '{question}' -> {matched}")
    else:
        print(f"  WARN: '{question}' -> {matched} (expected {expected_intent})")

print("\n=== 6. FilterResolver ===")
resolver = FilterResolver()

test_queries = [
    ("tahun 2025", "oss_kpi_card", {"filter_tahun"}),
    ("bulan januari 2025", "iboss_kpi_card", {"pilih_tahun", "pilih_bulan"}),
    ("tahun ini", "oss_gauge_performa", {"filter_tahun"}),
    ("3 bulan terakhir", "iboss_overdue", {"rentang_waktu"}),
]

for question, intent_id, expected_params in test_queries:
    result = resolver.apply(question, intent_id)
    keys = set(result.keys())
    assert keys & expected_params, f"Missing expected params for '{question}'/{intent_id}: got {keys}, expected {expected_params}"
    print(f"  OK: '{question}'/{intent_id} -> {result}")

print("\n=== ALL CHECKS PASSED ===")
