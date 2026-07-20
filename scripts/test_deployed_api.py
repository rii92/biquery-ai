"""Test deployed API with entity filters (izin type, status)."""
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
        print(f"  FAIL: '{query}' -> ERROR: {e}")
        return None
    intent = data.get("intent", "")
    sql = data.get("sql", "")
    reply = data.get("reply", "")
    elapsed = data.get("elapsed", 0)
    ok = bool(intent) and intent not in ("_greeting", "") and bool(sql)
    status = "OK" if ok else "FAIL"
    if ok:
        print(f"  OK:   '{query}'")
        print(f"         Intent: {intent} | {elapsed}s")
        print(f"         SQL: {sql[:120]}...")
        print(f"         Reply: {reply[:150]}")
    else:
        print(f"  FAIL: '{query}' -> intent={intent}, reply={reply[:100]}")
    print()
    return data

print("=== Deployed Entity Filter Tests ===\n")

tests = [
    "total izin PB bp batam",
    "total izin PL yang terbit bp batam",
    "total izin tolak bp batam",
    "total izin dalam proses bp batam",
    "total izin LALIN bp batam tahun 2025",
    "jumlah izin PB bulan januari 2025",
    "total izin PB 6 bulan terakhir",
    "flow izin PB bp batam",
    "kepatuhan SLA PB",
]

for q in tests:
    test(q)

print("=== Done ===")
