"""Validate intents.json loads correctly."""
import sys
sys.path.insert(0, ".")
from app.intents.loader import list_intents, get_intent

intents = list_intents()
print(f"Total intents: {len(intents)}")
for i in intents:
    print(f"  {i['id']:40s} source={i.get('source','?')} active={i.get('active')}")

# Check specific new intents
for oid in ["oss_kpi_card", "oss_gauge_performa", "oss_sebaran_jenis_perizinan",
            "oss_sebaran_risiko", "oss_sebaran_status_permohonan", "oss_tren_inflow_outflow",
            "oss_funnel_kemacetan", "oss_kepatuhan_sla", "oss_leaderboard_sla",
            "oss_rapor_staf", "oss_detail_permohonan"]:
    obj = get_intent(oid)
    assert obj is not None, f"Missing: {oid}"
    assert obj["source"] == "oss", f"Wrong source for {oid}: {obj['source']}"
    print(f"  OK: {oid}")

for iid in ["iboss_kpi_card", "iboss_overdue", "iboss_gauge_performa", "iboss_sebaran_status",
            "iboss_sebaran_proses", "iboss_tren_inflow_outflow", "iboss_funnel_kemacetan",
            "iboss_rata_waktu_role", "iboss_kepatuhan_sla", "iboss_leaderboard_sla",
            "iboss_sebaran_overdue", "iboss_total_overdue", "iboss_proporsi_kerja",
            "iboss_rapor_staf", "iboss_detail_permohonan"]:
    obj = get_intent(iid)
    assert obj is not None, f"Missing: {iid}"
    assert obj["source"] == "iboss", f"Wrong source for {iid}: {obj['source']}"
    print(f"  OK: {iid}")

print("\nAll intents validated successfully!")
