import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.config import WEBHOOK_SECRET

client = TestClient(app)

def test_webhook_rejects_bad_secret():
    response = client.post("/webhooks/ghl", json={}, headers={"X-Webhook-Secret": "wrong"})
    assert response.status_code == 401

def test_webhook_accepts_valid_secret():
    with patch("app.main.LeadModel") as mock_lead, \
         patch("app.main.ConversationModel") as mock_conv, \
         patch("app.main.debouncer") as mock_debouncer, \
         patch("app.main._log_event"):
        mock_lead.find_by_ghl_id.return_value = {"id": "uuid-1", "status": "nuevo", "assigned_agent": "setter"}
        mock_lead.refresh_window.return_value = {}
        mock_conv.get_active.return_value = {"id": "conv-1"}
        mock_conv.add_message.return_value = {}
        mock_debouncer.add = AsyncMock()
        response = client.post(
            "/webhooks/ghl",
            json={"direction": "inbound", "contactId": "c-1", "body": "Hola"},
            headers={"X-Webhook-Secret": WEBHOOK_SECRET},
        )
    assert response.status_code == 200

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
