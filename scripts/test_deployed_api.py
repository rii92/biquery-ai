"""Full filter test on deployed API."""
import json
import urllib.request
import base64

BASE = "http://172.18.32.172:8000"
AUTH = base64.b64encode(b"admin:12345").decode()

def test(query, expect_filters=None):
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
        print(f"  FAIL: '{query}' -> {e}")
        return None
    
    intent = data.get("intent", "")
    sql = data.get("sql", "")
    reply = data.get("reply", "")
    elapsed = data.get("elapsed", 0)
    
    where_idx = sql.find("WHERE")
    where_part = sql[where_idx:] if where_idx >= 0 else sql
    
    checks = []
    if expect_filters:
        for f in expect_filters:
            if f in where_part:
                checks.append(f"[OK] {f}")
            else:
                checks.append(f"[FAIL] {f} MISSING")
    
    has_data = "tidak ditemukan" not in reply.lower() and "belum didukung" not in reply.lower()
    all_ok = not expect_filters or all("[OK]" in c for c in checks)
    status = "OK" if (intent and has_data and all_ok) else "WARN" if intent and has_data else "FAIL"
    
    print(f"  {status}: '{query}'")
    print(f"         Intent: {intent} | {elapsed}s")
    if expect_filters:
        print(f"         Filters: {', '.join(checks)}")
    if intent and where_part.count("1 = 1") > 2:
        print(f"         [!] {where_part.count('1 = 1')}x '1=1' leftover")
    print(f"         Reply: {reply[:120]}...")
    return data

print("=" * 70)
print("DEPLOYED API -- FULL FILTER TEST")
print("=" * 70)
print()

# BP temporal
print("-- Temporal filters --")
test("total izin bp batam tahun 2025", expect_filters=["TO_CHAR(TGL_STATUS_TERAKHIR, 'YYYY') = '2025'"])
test("total izin bp batam 3 bulan terakhir", expect_filters=["TGL_STATUS_TERAKHIR) >= TO_DATE"])
test("jumlah izin bp batam bulan januari 2025", expect_filters=["TO_CHAR(TGL_STATUS_TERAKHIR, 'YYYY') = '2025'", "TO_CHAR(TGL_STATUS_TERAKHIR, 'MM') = '01'"])
test("total izin bp batam tahun ini")

# BP entity filters
print("\n-- Entity filters (izin type) --")
test("total izin PB bp batam", expect_filters=["UPPER(JENIS_IZIN) = UPPER('PB')"])
test("total izin PL bp batam", expect_filters=["UPPER(JENIS_IZIN) = UPPER('PL')"])
test("total izin LALIN bp batam tahun 2025", expect_filters=["UPPER(JENIS_IZIN) = UPPER('LALIN')", "TO_CHAR(TGL_STATUS_TERAKHIR, 'YYYY') = '2025'"])

# BP status filters
print("\n-- Entity filters (status) --")
test("total izin terbit bp batam", expect_filters=["KATEGORI_STATUS = 'TERBIT'"])
test("total izin tolak bp batam", expect_filters=["KATEGORI_STATUS = 'TOLAK'"])
test("total izin dalam proses bp batam", expect_filters=["KATEGORI_STATUS = 'DALAM PROSES'"])

# BP combination
print("\n-- Combination filters --")
test("total izin PB yang terbit bp batam", expect_filters=["UPPER(JENIS_IZIN) = UPPER('PB')", "KATEGORI_STATUS = 'TERBIT'"])
test("total izin PL tahun 2025", expect_filters=["UPPER(JENIS_IZIN) = UPPER('PL')", "TO_CHAR(TGL_STATUS_TERAKHIR, 'YYYY') = '2025'"])
test("jumlah izin PB bulan januari 2025", expect_filters=["UPPER(JENIS_IZIN) = UPPER('PB')", "TO_CHAR(TGL_STATUS_TERAKHIR, 'YYYY') = '2025'", "TO_CHAR(TGL_STATUS_TERAKHIR, 'MM') = '01'"])
test("total izin PB 6 bulan terakhir", expect_filters=["UPPER(JENIS_IZIN) = UPPER('PB')", "TRUNC(TGL_STATUS_TERAKHIR) >= TO_DATE"])

# Cross-intent
print("\n-- Cross-intent filters --")
test("flow izin PB bp batam", expect_filters=["UPPER(JENIS_IZIN) = UPPER('PB')"])
test("kepatuhan SLA PB", expect_filters=["UPPER(JENIS_IZIN) = UPPER('PB')"])
test("funnel PL bp batam", expect_filters=["UPPER(JENIS_IZIN) = UPPER('PL')"])
test("gauge performa PB", expect_filters=["UPPER(JENIS_IZIN) = UPPER('PB')"])
test("rapor staf PL", expect_filters=["UPPER(JENIS_IZIN) = UPPER('PL')"])

# OSS
print("\n-- OSS --")
test("kpi oss tahun 2025", expect_filters=["TAHUN = '2025'"])
test("total oss PB tahun 2025", expect_filters=["UPPER(JENIS_IZIN) = UPPER('PB')", "TAHUN = '2025'"])

# iBOSS
print("\n-- iBOSS --")
test("kpi iboss")
test("total iboss tahun 2025")

print("\n" + "=" * 70)
print("  DONE")
print("=" * 70)
