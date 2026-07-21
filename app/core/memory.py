"""In-memory conversation memory — stores last N exchanges per session."""

import time
from datetime import datetime
from typing import Dict, List, Optional


class Exchange:
    def __init__(self, user: str, assistant: str, intent: str, sql: str, payload: dict):
        self.user = user
        self.assistant = assistant
        self.intent = intent
        self.sql = sql
        self.payload = {k: v for k, v in payload.items() if v and k != "intent"}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "user": self.user,
            "assistant": self.assistant,
            "intent": self.intent,
            "sql": self.sql,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


_EXPIRY_SECONDS = 1800  # 30 menit


class ConversationMemory:
    def __init__(self, max_history: int = 3):
        self._store: Dict[str, List[Exchange]] = {}
        self.max_history = max_history

    def add(self, session_id: str, user: str, assistant: str, intent: str, sql: str, payload: dict):
        if session_id not in self._store:
            self._store[session_id] = []
        self._store[session_id].append(Exchange(user, assistant, intent, sql, payload))
        if len(self._store[session_id]) > self.max_history:
            self._store[session_id] = self._store[session_id][-self.max_history :]

    def get_history(self, session_id: str) -> List[Exchange]:
        self._expire(session_id)
        return self._store.get(session_id, [])

    def get_last(self, session_id: str) -> Optional[Exchange]:
        self._expire(session_id)
        history = self._store.get(session_id, [])
        return history[-1] if history else None

    def clear(self, session_id: str):
        self._store.pop(session_id, None)

    def _expire(self, session_id: str):
        if session_id not in self._store:
            return
        now = time.time()
        active = []
        for ex in self._store[session_id]:
            ts = datetime.fromisoformat(ex.timestamp).timestamp()
            if now - ts < _EXPIRY_SECONDS:
                active.append(ex)
        if active:
            self._store[session_id] = active
        else:
            del self._store[session_id]


def history_to_text(history: List[Exchange], current_question: str) -> str:
    """Format conversation history as text for LLM context."""
    if not history:
        return ""
    lines = ["Percakapan sebelumnya:"]
    for ex in history:
        lines.append(f"User: {ex.user}")
        lines.append(f"Assistant: {ex.assistant[:200]}")
    lines.append("")
    lines.append(f"Pertanyaan saat ini: {current_question}")
    return "\n".join(lines)


# Singleton global
_memory = ConversationMemory()


def get_memory() -> ConversationMemory:
    return _memory
