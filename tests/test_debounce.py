import pytest
import asyncio
from unittest.mock import AsyncMock
from app.orchestrator.debounce import Debouncer

@pytest.mark.asyncio
async def test_debounce_groups_messages():
    handler = AsyncMock()
    debouncer = Debouncer(delay_seconds=0.1, handler=handler)
    await debouncer.add("lead-1", "Hola")
    await debouncer.add("lead-1", "¿cómo estás?")
    await asyncio.sleep(0.2)
    handler.assert_called_once_with("lead-1", ["Hola", "¿cómo estás?"])

@pytest.mark.asyncio
async def test_debounce_separate_leads():
    handler = AsyncMock()
    debouncer = Debouncer(delay_seconds=0.1, handler=handler)
    await debouncer.add("lead-1", "Hola")
    await debouncer.add("lead-2", "Buenos días")
    await asyncio.sleep(0.2)
    assert handler.call_count == 2
