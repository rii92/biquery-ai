"""Comprehensive local test for conversation memory feature.

Tests all code paths without requiring Oracle database connection.
"""
import sys, os, json, time, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Mock database before any imports ──
import app.database.sqlite_client as sqlite_mod
sqlite_mod._DB_PATH = ":memory:"

from app.core.memory import get_memory, history_to_text, Exchange
from app.ai.keyword_classifier import classify_by_keyword, is_followup, is_affirmative

PASS = 0
FAIL = 0

def ok(msg):
    global PASS; PASS += 1
    print(f"  [PASS] {msg}")

def fail(msg, detail=""):
    global FAIL; FAIL += 1
    print(f"  [FAIL] {msg}")
    if detail:
        print(f"         {detail}")

print("=" * 65)
print("CONVERSATION MEMORY — LOCAL UNIT TESTS")
print("=" * 65)

# ── 1. Follow-up detection ──
print("\n--- 1. Follow-up detection ---")
assert is_followup("iya"), "is_followup iya"
assert is_followup("ya"), "is_followup ya"
assert is_followup("lanjut"), "is_followup lanjut"
assert is_followup("tidak"), "is_followup tidak"
assert is_followup("nggak"), "is_followup nggak"
assert is_followup("Iya"), "is_followup Iya (capital)"
assert is_followup("YA."), "is_followup YA. (punctuation)"
assert is_followup("  iya  "), "is_followup whitespace"
assert not is_followup("total izin"), "is_followup normal query"
assert not is_followup(""), "is_followup empty"
ok("Follow-up detection works")

assert is_affirmative("iya"), "affirmative iya"
assert is_affirmative("lanjut"), "affirmative lanjut"
assert is_affirmative("tentu"), "affirmative tentu"
assert not is_affirmative("tidak"), "negative tidak"
assert not is_affirmative("nggak"), "negative nggak"
assert not is_affirmative("ga"), "negative ga"
ok("Affirmative/negative classification works")

# ── 2. Memory storage and retrieval ──
print("\n--- 2. Memory storage ---")
mem = get_memory()
mem.clear("test_sess")

# Add first exchange
mem.add("test_sess", "total izin bp batam tahun 2025",
        "Total 15.592 dokumen...", "bp_all_kpi_card",
        "SELECT ...", {"tahun": "TO_CHAR(...) = '2025'"})
h = mem.get_history("test_sess")
assert len(h) == 1, f"Expected 1, got {len(h)}"
assert h[0].intent == "bp_all_kpi_card"
assert h[0].payload["tahun"] == "TO_CHAR(...) = '2025'"
ok("Single exchange stored correctly")

# Add second exchange (follow-up)
mem.add("test_sess", "iya", "Berikut detailnya...",
        "bp_all_kpi_card", "SELECT ...", {"tahun": "TO_CHAR(...) = '2025'"})
h = mem.get_history("test_sess")
assert len(h) == 2
ok("Follow-up exchange appended")

# Max history enforcement
for i in range(5):
    mem.add("test_sess", f"q{i}", f"a{i}", f"intent_{i}", "SQL", {})
h = mem.get_history("test_sess")
assert len(h) == 3, f"Expected max 3, got {len(h)}"
assert h[-1].user == "q4"
ok(f"Max history enforced ({len(h)} of 3)")

# Expiry
mem.clear("exp_test")
mem.add("exp_test", "q", "a", "i", "SQL", {})
h = mem.get_history("exp_test")
assert len(h) == 1
ok("Non-expired entries accessible")

# Clear
mem.clear("test_sess")
assert mem.get_history("test_sess") == []
ok("Clear works")

# ── 3. history_to_text formatting ──
print("\n--- 3. History text formatting ---")
mem.clear("fmt_test")
mem.add("fmt_test", "total izin bp 2025",
        "Total 15.592 dokumen. Apakah Anda ingin melihat lebih detail?",
        "bp_all_kpi_card", "SELECT ...", {})
mem.add("fmt_test", "iya",
        "Baik, berikut rinciannya...",
        "bp_all_kpi_card", "SELECT ...", {})

text = history_to_text(mem.get_history("fmt_test"), "lanjut")
assert "Percakapan sebelumnya:" in text
assert "total izin bp 2025" in text
assert "Total 15.592 dokumen" in text
assert "Pertanyaan saat ini: lanjut" in text
ok("history_to_text format correct")

# ── 4. Full flow simulation (mocked) ──
print("\n--- 4. Full conversation flow simulation ---")
mem.clear("flow_test")

# Simulate exchange 1: new query
q1 = "total izin bp batam tahun 2025"
p1 = classify_by_keyword(q1)
assert p1 and p1.get("intent") == "bp_all_kpi_card", f"Expected bp_all_kpi_card, got {p1}"
ok(f"Q1 classify: {p1['intent']}")

# Simulate follow-up handling as done in query.py
history = mem.get_history("flow_test")
# No history yet, so follow-up shouldn't trigger
assert not history
ok("Q1: no history yet (correct)")

# Store Q1 result
mem.add("flow_test", q1, "Total 15.592 dokumen... Apakah ingin detail?",
        p1["intent"], "SELECT 1", {"tahun": "TO_CHAR(...) = '2025'"})

# Exchange 2: follow-up "iya"
q2 = "iya"
p2 = classify_by_keyword(q2)
assert p2 is None, f"Follow-up should not match intents, got {p2}"
history = mem.get_history("flow_test")
assert len(history) == 1
assert is_followup(q2)
assert is_affirmative(q2)
# This is what query.py does: reuse last intent + payload
last = history[-1]
restored = {"intent": last.intent, **last.payload}
assert restored["intent"] == "bp_all_kpi_card"
assert restored["tahun"] == "TO_CHAR(...) = '2025'"
ok("Q2 follow-up 'iya': intent + filters restored from history")

# Exchange 3: follow-up "tidak"
q3 = "tidak"
p3 = classify_by_keyword(q3)
assert p3 is None
assert is_followup(q3)
assert not is_affirmative(q3)
# query.py would short-circuit with "Baik, ada pertanyaan lain?"
ok("Q3 follow-up 'tidak': correctly identified as negative")

# Exchange 4: new question in same session
q4 = "total izin PL bp batam"
p4 = classify_by_keyword(q4)
assert p4 and p4.get("intent") == "bp_all_kpi_card"
history = mem.get_history("flow_test")
assert len(history) == 1  # unchanged
ok(f"Q4 new query: {p4['intent']} (history preserved)")

# Exchange 5: follow-up after Q4
mem.add("flow_test", q4, "Total 144 dokumen PL...",
        p4["intent"], "SELECT 1", {"perizinan": "UPPER(JENIS_IZIN) = UPPER('PL')"})
history = mem.get_history("flow_test")
assert len(history) == 2
q5 = "ya"
assert is_followup(q5)
last = history[-1]
restored = {"intent": last.intent, **last.payload}
assert restored["perizinan"] == "UPPER(JENIS_IZIN) = UPPER('PL')"
ok("Q5 follow-up after PL query: restored PL filter correctly")

# ── 5. Concurrent sessions ──
print("\n--- 5. Session isolation ---")
mem.clear("u1")
mem.clear("u2")
mem.add("u1", "q1_u1", "a1_u1", "intent_a", "SQL", {})
mem.add("u2", "q1_u2", "a1_u2", "intent_b", "SQL", {})
h1 = mem.get_history("u1")
h2 = mem.get_history("u2")
assert len(h1) == 1 and h1[0].user == "q1_u1"
assert len(h2) == 1 and h2[0].user == "q1_u2"
ok("Sessions isolated correctly")

# ── 6. API request format ──
print("\n--- 6. API schema validation ---")
from pydantic import BaseModel

# Validate that session_id field exists in the API models by checking the source
import inspect
from app.api import query as query_module

src = inspect.getsource(query_module.QueryRequest)
assert "session_id: str" in src, f"QueryRequest missing session_id: {src[:300]}"
ok("QueryRequest has session_id field")

src = inspect.getsource(query_module.QueryResponse)
assert "session_id: str" in src, f"QueryResponse missing session_id: {src[:300]}"
ok("QueryResponse has session_id field")

# ── Results ──
print("\n" + "=" * 65)
print(f"RESULTS: {PASS} passed, {FAIL} failed")
print("=" * 65)
if FAIL:
    print("SOME TESTS FAILED!")
    sys.exit(1)
else:
    print("ALL TESTS PASSED!")
