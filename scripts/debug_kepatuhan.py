import sys; sys.path.insert(0, ".")
import re
from app.intents.loader import list_active_intents, find_intent_by_keywords

q = "kepatuhan SLA PB"
ql = q.lower()
print(f"Query: {q!r}")
print(f"Lower: {ql!r}")
print()

for i in list_active_intents():
    for pat in i["keyword_patterns"]:
        try:
            m = re.search(pat, ql)
            status = "MATCH" if m else "no"
            if status == "MATCH":
                print(f"MATCH: {i['id']}: {pat!r}")
        except Exception as e:
            print(f"ERROR: {i['id']}: {pat!r} -> {e}")

print()
result = find_intent_by_keywords(q)
print(f"Final result: {result}")
