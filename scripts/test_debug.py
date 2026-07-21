import json, urllib.request, base64

BASE = "http://172.18.32.172:8000"
AUTH = base64.b64encode(b"admin:12345").decode()

def send(msg):
    body = json.dumps({"message": msg}).encode()
    req = urllib.request.Request(
        BASE + "/api/query", data=body,
        headers={"Authorization": f"Basic {AUTH}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())

tests = [
    "total izin bp batam tahun 2025",
    "total izin PB bp batam",
    "total izin terbit bp batam",
    "total izin PB yang terbit bp batam",
    "kpi oss tahun 2025",
]

for q in tests:
    print(f"=== {q} ===")
    data = send(q)
    sql = data.get("sql", "")
    print(f"Intent: {data.get('intent', 'N/A')}")
    print(f"Elapsed: {data.get('elapsed', 0)}s")
    # Print WHERE clause
    where_idx = sql.find("WHERE")
    if where_idx >= 0:
        print(f"WHERE: {sql[where_idx:]}")
    else:
        print(f"SQL (full): {sql}")
    reply = data.get("reply", "")
    print(f"Reply: {reply[:200]}")
    print()
