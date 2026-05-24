"""Integration test for the /webhook/whatsapp endpoint (mocked Ollama)."""
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@patch("app.ai.intent_extractor.httpx.post")
def test_webhook_known_intent(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "response": '{"intent": "count_students", "params": {}}'
    }
    resp = client.post("/webhook/whatsapp", json={
        "sender": "628123456789",
        "message": "Berapa jumlah siswa?"
    })
    assert resp.status_code == 200
    assert "reply" in resp.json()


@patch("app.ai.intent_extractor.httpx.post")
def test_webhook_unknown_intent(mock_post):
    mock_post.side_effect = Exception("connection error")
    resp = client.post("/webhook/whatsapp", json={
        "sender": "628123456789",
        "message": "Hapus semua siswa"
    })
    assert resp.status_code == 200
    assert isinstance(resp.json()["reply"], str)
