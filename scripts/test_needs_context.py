import sys
sys.path.insert(0, r"D:\planning-project\paijo\eduquery-ai")
from app.ai.keyword_classifier import is_followup, is_affirmative, needs_context

tests = [
    ("apa yang bisa direkomendasikan dari ini", False, True, True),
    ("apa rekomendasi dari data tersebut", False, True, True),
    ("rekomendasi untuk pb 2026", False, True, True),
    ("bagaimana rekomendasi selanjutnya", False, True, True),
    ("berdasarkan data ini apa yang disarankan", False, True, True),
    ("saya mau lihat data izin bp batam", False, True, True),  # 7 words < 8 → ctx=True
]

ok = True
for q, exp_follow, exp_affirm, exp_ctx in tests:
    follow = is_followup(q)
    affirm = is_affirmative(q)
    ctx = needs_context(q)
    status = follow == exp_follow and affirm == exp_affirm and ctx == exp_ctx
    if not status:
        ok = False
        print(f"  [FAIL] {q!r}: follow={follow}({exp_follow}) affirm={affirm}({exp_affirm}) ctx={ctx}({exp_ctx})")
    else:
        print(f"  [PASS] {q!r}")

print()
print("All passed!" if ok else "SOME FAILURES")
