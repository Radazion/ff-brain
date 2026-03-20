import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.agents.setter import SetterAgent

@pytest.fixture
def setter():
    return SetterAgent()

@pytest.fixture
def lead_with_form():
    return {
        "id": "uuid-1",
        "ghl_contact_id": "ghl-1",
        "name": "María",
        "status": "nuevo",
        "source": "form",
        "funnel_stage": "lleno_form",
        "qualification_score": 0,
        "form_data": {"diabetes_type": "tipo_2"},
        "window_open_until": "2099-01-01T00:00:00+00:00",
    }

@pytest.mark.asyncio
async def test_setter_first_contact_with_form(setter, lead_with_form):
    with patch("app.agents.base.ConversationModel") as mock_conv, \
         patch("app.agents.base.get_config", return_value=20), \
         patch("app.agents.setter.build_setter_prompt", return_value="system"), \
         patch("app.services.claude.get_anthropic") as mock_anthropic, \
         patch.object(setter, "send_response", new_callable=AsyncMock) as mock_send, \
         patch("app.agents.setter.LeadModel"):
        mock_conv.get_active.return_value = None
        mock_conv.create.return_value = {"id": "conv-1"}
        mock_conv.get_recent_messages.return_value = []
        mock_conv.add_message.return_value = {}
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="¡Hola María! Vi que completaste el formulario")]
        mock_anthropic.return_value.messages.create = AsyncMock(return_value=mock_response)
        await setter.process(lead_with_form, "[FORM_COMPLETED]")
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_setter_updates_status(setter, lead_with_form):
    with patch("app.agents.base.ConversationModel") as mock_conv, \
         patch("app.agents.base.get_config", return_value=20), \
         patch("app.agents.setter.build_setter_prompt", return_value="system"), \
         patch("app.services.claude.get_anthropic") as mock_anthropic, \
         patch.object(setter, "send_response", new_callable=AsyncMock), \
         patch("app.agents.setter.LeadModel") as mock_lead:
        mock_conv.get_active.return_value = None
        mock_conv.create.return_value = {"id": "conv-1"}
        mock_conv.get_recent_messages.return_value = []
        mock_conv.add_message.return_value = {}
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Hola")]
        mock_anthropic.return_value.messages.create = AsyncMock(return_value=mock_response)
        await setter.process(lead_with_form, "[FORM_COMPLETED]")
        mock_lead.update_status.assert_called_with("uuid-1", "en_calificacion")

def test_parse_actions():
    setter = SetterAgent()
    text = "Hola María\n[ACTION:update_score:+3:tiene diabetes]\nTe cuento..."
    clean, actions = setter._parse_actions(text)
    assert "Hola María" in clean
    assert "[ACTION" not in clean
    assert len(actions) == 1
    assert actions[0]["type"] == "update_score"

def test_should_escalate():
    setter = SetterAgent()
    assert setter._should_escalate("quiero hablar con alguien") is True
    assert setter._should_escalate("hola como estas") is False
