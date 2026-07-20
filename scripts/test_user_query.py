"""Test the exact user query."""
import sys
sys.path.insert(0, ".")
from app.ai.keyword_classifier import classify_by_keyword
from app.intents.loader import get_intent
from app.ai.filter_resolver import FilterResolver

query = "total izin bp batam tahun 2025"
print(f"Query: {query!r}")

result = classify_by_keyword(query)
if result:
    intent_id = result["intent"]
    print(f"  Intent matched: {intent_id}")
    meta = get_intent(intent_id)
    print(f"  SQL params: {list(meta['params'].keys())}")
else:
    print("  No intent matched by keywords")

resolver = FilterResolver()
filters = resolver.apply(query, intent_id if result else bp_all_kpi_card)
print(f"  Filters: {filters}")

if result:
    from app.services.bp_database_service import BPDatabaseService
    svc = BPDatabaseService()
    payload = {"intent": intent_id, **filters}
    sql = svc.generate_sql(payload)
    print(f"  SQL: {sql[:300]}...")
    remaining = [p for p in meta["params"] if "{" + p + "}" in sql]
    print(f"  Unresolved params: {remaining}")
