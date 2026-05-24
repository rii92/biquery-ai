"""Unit test untuk ekstraksi intent (HTTP di-mock)."""
from unittest.mock import patch

from app.services.intent_service import IntentService


@patch("app.ai.intent_extractor.httpx.post")
def test_count_students_extract(mock_post):
    # Pakai query yang tidak cocok dengan keyword classifier
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "response": '{"intent": "count_students", "params": {}}'
    }
    svc = IntentService()
    result = svc.extract("Hitung total siswa")
    assert result["intent"] == "count_students"


@patch("app.ai.intent_extractor.httpx.post")
def test_unknown_intent_on_error(mock_post):
    mock_post.side_effect = Exception("connection error")
    svc = IntentService()
    result = svc.extract("Hapus semua data")
    assert result["intent"] == ""
