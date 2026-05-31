"""Full end-to-end test for DMT1 intents + insight templates."""
import json
from app.main import app
from app.ai.keyword_classifier import classify_by_keyword
from app.services.insight_service import InsightService
from app.intents.loader import get_intent, list_intents

print("=== 1. All intents ===")
intents = list_intents()
print(f"  Total: {len(intents)}")
print(f"  IDs: {[i['id'] for i in intents]}")

print("\n=== 2. DMT1 SQL templates ===")
for iid in ["DMT1_total_izin", "DMT1_total_terbit", "DMT1_total_tolak",
            "DMT1_total_proses_pelaku_usaha", "DMT1_total_dalam_proses",
            "DMT1_row_izin_by_status", "DMT1_komposisi_keseluruhan_izin"]:
    meta = get_intent(iid)
    print(f"  {iid:40s} {'OK' if meta else 'MISSING'}")

print("\n=== 3. DMT1 keyword classification ===")
tests = [
    ("total izin bp batam", "DMT1_total_izin"),
    ("total izin terbit bp batam", "DMT1_total_terbit"),
    ("total izin ditolak", "DMT1_total_tolak"),
    ("total izin proses pelaku usaha", "DMT1_total_proses_pelaku_usaha"),
    ("total izin dalam proses", "DMT1_total_dalam_proses"),
    ("sebaran izin per jenis dan status", "DMT1_row_izin_by_status"),
    ("komposisi keseluruhan izin", "DMT1_komposisi_keseluruhan_izin"),
    ("halo", "_greeting"),
    ("total masuk izin bp batam", "bp_total_masuk"),
    ("backlog bp batam", "bp_total_backlog_per_bulan"),
    ("izin terbit per minggu bp batam", "bp_izin_terbit_per_bulan"),
]
all_ok = True
for q, expected in tests:
    r = classify_by_keyword(q)
    got = r["intent"] if r else "None"
    ok = got == expected
    if not ok:
        all_ok = False
    print(f'  {"OK" if ok else "MIS"}  {q:45s} -> {got} (expected {expected})')
print(f"  All OK: {all_ok}")

print("\n=== 4. DMT1 deterministic insight ===")
s = InsightService()
d1 = s.deterministic({"intent": "DMT1_total_izin"}, [{"TOTAL_PERIZINAN": 1500}])
print(f"  total_izin: {d1}")
d2 = s.deterministic({"intent": "DMT1_total_terbit"}, [{"TOTAL_TERBIT": 750}])
print(f"  total_terbit: {d2}")
d3 = s.deterministic({"intent": "DMT1_row_izin_by_status"}, [
    {"JENIS_IZIN": "PB", "KELOMPOK_STATUS": "Terbit", "JUMLAH": 500},
    {"JENIS_IZIN": "PKKPRL", "KELOMPOK_STATUS": "Dalam Proses", "JUMLAH": 300},
])
print(f"  row_izin_by_status: {d3}")

print("\n=== 5. templates.json rules ===")
t = s.templates
dmt_keys = [k for k in t.get("intent_rules", {}) if k.startswith("DMT1") or k == "_default"]
print(f"  DMT1+default rules: {dmt_keys}")

print("\n=== ALL CHECKS DONE ===")
