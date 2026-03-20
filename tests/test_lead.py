from unittest.mock import patch, MagicMock
from app.models.lead import LeadModel

def test_create_lead(mock_supabase, sample_lead_data):
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{**sample_lead_data, "id": "uuid-1", "status": "nuevo"}]
    )
    with patch("app.models.lead.get_supabase", return_value=mock_supabase):
        lead = LeadModel.create(sample_lead_data)
    assert lead["ghl_contact_id"] == "ghl_123"
    assert lead["status"] == "nuevo"

def test_find_by_phone(mock_supabase):
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "uuid-1", "phone": "+5491155551234", "name": "María"}]
    )
    with patch("app.models.lead.get_supabase", return_value=mock_supabase):
        lead = LeadModel.find_by_phone("+5491155551234")
    assert lead is not None
    assert lead["name"] == "María"

def test_find_by_phone_not_found(mock_supabase):
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[]
    )
    with patch("app.models.lead.get_supabase", return_value=mock_supabase):
        lead = LeadModel.find_by_phone("+0000000000")
    assert lead is None

def test_update_status(mock_supabase):
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "uuid-1", "status": "en_calificacion"}]
    )
    with patch("app.models.lead.get_supabase", return_value=mock_supabase):
        lead = LeadModel.update_status("uuid-1", "en_calificacion")
    assert lead["status"] == "en_calificacion"

def test_update_window(mock_supabase):
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    expected = now + timedelta(hours=24)
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "uuid-1", "window_open_until": expected.isoformat()}]
    )
    with patch("app.models.lead.get_supabase", return_value=mock_supabase):
        lead = LeadModel.refresh_window("uuid-1")
    assert lead["window_open_until"] is not None
