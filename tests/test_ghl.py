import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.ghl import GHLClient

@pytest.fixture
def ghl():
    return GHLClient()

@pytest.mark.asyncio
async def test_send_message(ghl):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"messageId": "msg-1"}
    mock_response.raise_for_status = MagicMock()
    with patch.object(ghl.http, "post", new_callable=AsyncMock, return_value=mock_response):
        result = await ghl.send_message("contact-1", "Hola María")
    assert result["messageId"] == "msg-1"

@pytest.mark.asyncio
async def test_get_contact(ghl):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"contact": {"id": "contact-1", "name": "María"}}
    mock_response.raise_for_status = MagicMock()
    with patch.object(ghl.http, "get", new_callable=AsyncMock, return_value=mock_response):
        contact = await ghl.get_contact("contact-1")
    assert contact["name"] == "María"

@pytest.mark.asyncio
async def test_send_template(ghl):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"messageId": "msg-2"}
    mock_response.raise_for_status = MagicMock()
    with patch.object(ghl.http, "post", new_callable=AsyncMock, return_value=mock_response):
        result = await ghl.send_template("contact-1", "reminder_24h", {"name": "María", "hora": "10:00"})
    assert result["messageId"] == "msg-2"

def test_is_human_message():
    assert GHLClient.is_human_message({"type": "manual", "direction": "outbound"}) is True
    assert GHLClient.is_human_message({"type": "api", "direction": "outbound"}) is False
    assert GHLClient.is_human_message({"direction": "inbound"}) is False
