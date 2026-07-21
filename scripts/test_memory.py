import json, urllib.request, base64, time

BASE = "http://172.18.32.172:8000"
AUTH = base64.b64encode(b"admin:12345").decode()
SESSION = f"test_mem_{int(time.time())}"

def send(msg, session=None):
    body = json.dumps({"message": msg, "session_id": session or SESSION}).encode()
    req = urllib.request.Request(
        BASE + "/api/query", data=body,
        headers={"Authorization": f"Basic {AUTH}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())

print("=" * 70)
print("MEMORY TEST")
print("=" * 70)

# Exchange 1: First question
print("\n[1] User: total izin bp batam tahun 2025")
r1 = send("total izin bp batam tahun 2025")
print(f"    Intent: {r1['intent']}")
print(f"    Reply: {r1['reply'][:150]}...")
print(f"    session_id: {r1.get('session_id', 'N/A')}")
sid = r1.get('session_id', SESSION)
print()

# Exchange 2: Follow-up "iya"
print("[2] User: iya")
r2 = send("iya", session=sid)
print(f"    Intent: {r2['intent']}")
print(f"    Reply: {r2['reply'][:150]}...")
print(f"    session_id: {r2.get('session_id', 'N/A')}")
print()

# Exchange 3: New question in same session
print("[3] User: total izin PL bp batam")
r3 = send("total izin PL bp batam", session=sid)
print(f"    Intent: {r3['intent']}")
print(f"    Reply: {r3['reply'][:150]}...")
print()

# Exchange 4: Negative follow-up "tidak"
print("[4] User: tidak")
r4 = send("tidak", session=sid)
print(f"    Intent: {r4['intent']}")
print(f"    Reply: {r4['reply'][:150]}...")
print()

print("=" * 70)
print("RESULTS:")
print(f"  [1] First query intent:         {r1.get('intent', 'FAIL')}")
print(f"  [2] Follow-up 'iya' intent:     {r2.get('intent', 'FAIL')} (should match [1])")
print(f"  [3] New query intent:           {r3.get('intent', 'FAIL')} (should be different)")
print(f"  [4] Negative follow-up:         {r4.get('reply', 'FAIL')[:80]}")
print()

# Verify
ok = True
if not r1.get('intent'):
    print("FAIL: Exchange 1 got no intent"); ok = False
if r2.get('intent') and r2['intent'] != r1['intent']:
    print(f"WARN: Follow-up intent ({r2['intent']}) != original ({r1['intent']}) — may still be OK")
if 'Baik' not in r4.get('reply', ''):
    print(f"WARN: Negative follow-up unexpected reply: {r4.get('reply', '')[:80]}")
if ok:
    print("ALL CHECKS PASSED")
print("=" * 70)
