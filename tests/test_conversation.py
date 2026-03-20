from unittest.mock import patch, MagicMock
from app.models.conversation import ConversationModel

def test_create_conversation(mock_supabase):
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "conv-1", "lead_id": "uuid-1", "agent": "setter", "status": "active"}]
    )
    with patch("app.models.conversation.get_supabase", return_value=mock_supabase):
        conv = ConversationModel.create("uuid-1", "setter")
    assert conv["agent"] == "setter"
    assert conv["status"] == "active"

def test_get_active_conversation(mock_supabase):
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "conv-1", "lead_id": "uuid-1", "status": "active"}]
    )
    with patch("app.models.conversation.get_supabase", return_value=mock_supabase):
        conv = ConversationModel.get_active("uuid-1")
    assert conv is not None

def test_add_message(mock_supabase):
    msg_table = MagicMock()
    conv_table = MagicMock()
    msg_table.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "msg-1", "role": "lead", "content": "Hola"}]
    )
    conv_table.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])

    def table_side_effect(name):
        if name == "messages":
            return msg_table
        return conv_table

    mock_supabase.table.side_effect = table_side_effect
    with patch("app.models.conversation.get_supabase", return_value=mock_supabase):
        msg = ConversationModel.add_message("conv-1", "lead", "Hola")
    assert msg["content"] == "Hola"

def test_get_recent_messages(mock_supabase):
    messages = [
        {"id": f"msg-{i}", "role": "lead" if i % 2 else "bot", "content": f"msg {i}"}
        for i in range(5)
    ]
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
        data=messages
    )
    with patch("app.models.conversation.get_supabase", return_value=mock_supabase):
        recent = ConversationModel.get_recent_messages("conv-1", limit=20)
    assert len(recent) == 5
