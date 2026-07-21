"""Quick test for memory auto-reset after MAX_EXCHANGES."""
import sys
sys.path.insert(0, r"D:\planning-project\paijo\eduquery-ai")

from app.core.memory import ConversationMemory, MAX_EXCHANGES_BEFORE_RESET

print(f"MAX_EXCHANGES_BEFORE_RESET = {MAX_EXCHANGES_BEFORE_RESET}\n")

mem = ConversationMemory(max_history=3)
sid = "test_user"

# Simulate N exchanges
for i in range(1, MAX_EXCHANGES_BEFORE_RESET + 2):
    reset = mem.check_and_reset(sid)
    h = mem.get_history(sid)
    print(f"Exchange {i}: reset={reset}, history_len={len(h)}")
    if reset:
        print(f"  Memory cleared! Starting fresh.\n")
    else:
        mem.add(sid, f"Q{i}", f"A{i}", "bp_all_kpi_card", "SELECT 1", {"intent": "bp_all_kpi_card"})

print("Test complete.")
