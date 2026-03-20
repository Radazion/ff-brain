import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.agents.intel import IntelAgent

@pytest.fixture
def intel():
    return IntelAgent()

@pytest.mark.asyncio
async def test_analyze_conversation_extracts_objections(intel):
    mock_messages = [
        {"role": "bot", "content": "¿Me contás cómo venís?"},
        {"role": "lead", "content": "Bien pero cuánto sale esto?"},
        {"role": "bot", "content": "El costo se ajusta a cada caso"},
        {"role": "lead", "content": "Dale, agendemos"},
    ]
    claude_response = '{"objections": [{"text": "cuánto sale esto", "category": "precio", "resolved": true, "resolution": "reframe inversión"}], "questions": [{"text": "cuánto sale", "category": "precio"}], "engagement_score": 7, "buy_signals": ["agendemos"], "drop_reason": null, "summary": "Lead preguntó precio, se resolvió, agendó"}'

    with patch("app.agents.intel.ConversationModel") as mock_conv, \
         patch("app.agents.intel.claude") as mock_claude, \
         patch("app.agents.intel.IntelModels") as mock_intel, \
         patch("app.agents.intel.LeadModel") as mock_lead:
        mock_lead.get.return_value = {"status": "agendado"}
        mock_conv.get_recent_messages.return_value = mock_messages
        mock_claude.chat = AsyncMock(return_value=claude_response)
        await intel.analyze_conversation("conv-1", "lead-1")
        mock_intel.save_objection.assert_called_once()
        mock_intel.save_question.assert_called_once()
        mock_intel.save_conversation_score.assert_called_once()
