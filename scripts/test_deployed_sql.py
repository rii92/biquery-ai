"""Test deployed API and verify SQL filters are actually applied."""
import json
import urllib.request
import base64

BASE = "http://172.18.32.172:8000"
AUTH = base64.b64encode(b"admin:12345").decode()

def test(query):
    url = BASE + "/api/query"
    body = json.dumps({"message": query}).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Authorization": f"Basic {AUTH}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"FAIL: '{query}' -> {e}")
        return None
    intent = data.get("intent", "")
    sql = data.get("sql", "")
    reply = data.get("reply", "")
    elapsed = data.get("elapsed", 0)
    
    print(f"Query: {query}")
    print(f"  Intent: {intent} | {elapsed}s")
    
    # Check SQL for filter clauses
    has_filter = False
    for kw in ["UPPER(JENIS_IZIN)", "KATEGORI_STATUS", "1 = 1"]:
        if kw in sql:
            has_filter = True
            print(f"  SQL contains: {kw}")
    
    # Find the WHERE clause part
    where_idx = sql.find("WHERE")
    if where_idx >= 0:
        where_part = sql[where_idx:]
        print(f"  WHERE clause: {where_part[:300]}")
    
    print(f"  Reply preview: {reply[:200]}")
    print()
    return data

print("=== Checking if filters actually applied in SQL ===\n")

tests = [
    "total izin PB bp batam",
    "total izin PL yang terbit bp batam",
    "total izin tolak bp batam",
    "total izin LALIN bp batam tahun 2025",
    "jumlah izin PB bulan januari 2025",
    "total izin PB 6 bulan terakhir",
]

for q in tests:
    test(q)

print("=== Done ===")
