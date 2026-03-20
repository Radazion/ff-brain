import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_supabase():
    client = MagicMock()
    table_mock = MagicMock()
    table_mock.select.return_value = table_mock
    table_mock.insert.return_value = table_mock
    table_mock.update.return_value = table_mock
    table_mock.upsert.return_value = table_mock
    table_mock.eq.return_value = table_mock
    table_mock.single.return_value = table_mock
    table_mock.execute.return_value = MagicMock(data=[])
    client.table.return_value = table_mock
    return client

@pytest.fixture
def sample_lead_data():
    return {
        "ghl_contact_id": "ghl_123",
        "name": "María García",
        "phone": "+5491155551234",
        "email": "maria@test.com",
        "source": "form",
        "form_data": {"diabetes_type": "tipo_2", "hba1c": "7.2"}
    }
