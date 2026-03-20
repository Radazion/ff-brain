import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.agents.post_agenda import PostAgendaAgent

@pytest.fixture
def agent():
    return PostAgendaAgent()

@pytest.fixture
def appointment():
    return {
        "id": "apt-1",
        "lead_id": "uuid-1",
        "scheduled_at": "2026-03-25T15:00:00+00:00",
        "zoom_link": "https://zoom.us/j/123",
        "show_status": "pending",
        "rescue_attempts": 0,
    }

@pytest.mark.asyncio
async def test_noshow_sends_rescue(agent, appointment):
    with patch("app.agents.post_agenda.LeadModel") as mock_lead, \
         patch("app.agents.post_agenda.AppointmentModel") as mock_apt, \
         patch("app.agents.post_agenda.get_config", return_value=2), \
         patch("app.agents.post_agenda.GHLClient") as mock_ghl:
        mock_lead.get.return_value = {"id": "uuid-1", "ghl_contact_id": "ghl-1", "name": "María"}
        mock_ghl_instance = MagicMock()
        mock_ghl_instance.send_template = AsyncMock()
        mock_ghl.return_value = mock_ghl_instance
        await agent.handle_noshow(appointment)
        mock_ghl_instance.send_template.assert_called_once()
        mock_apt.update.assert_called_once()

@pytest.mark.asyncio
async def test_noshow_max_attempts_archives(agent):
    appointment = {
        "id": "apt-1", "lead_id": "uuid-1",
        "rescue_attempts": 2, "show_status": "no_show"
    }
    with patch("app.agents.post_agenda.LeadModel") as mock_lead, \
         patch("app.agents.post_agenda.get_config", return_value=2):
        mock_lead.get.return_value = {"id": "uuid-1", "name": "María"}
        await agent.handle_noshow(appointment)
        mock_lead.update_status.assert_called_with("uuid-1", "dormido")
