import asyncio
import logging
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)

class Debouncer:
    def __init__(self, delay_seconds: float = 15.0,
                 handler: Callable[[str, list[str]], Awaitable] = None):
        self.delay = delay_seconds
        self.handler = handler
        self._buffers: dict[str, list[str]] = {}
        self._timers: dict[str, asyncio.Task] = {}

    async def add(self, lead_id: str, message: str):
        if lead_id not in self._buffers:
            self._buffers[lead_id] = []
        self._buffers[lead_id].append(message)
        if lead_id in self._timers:
            self._timers[lead_id].cancel()
        self._timers[lead_id] = asyncio.create_task(self._flush(lead_id))

    async def _flush(self, lead_id: str):
        await asyncio.sleep(self.delay)
        messages = self._buffers.pop(lead_id, [])
        self._timers.pop(lead_id, None)
        if messages and self.handler:
            try:
                await self.handler(lead_id, messages)
            except Exception as e:
                logger.error(f"Debouncer handler failed for lead {lead_id}: {e}", exc_info=True)
                from app.services.supabase_client import get_supabase
                try:
                    get_supabase().table("event_log").insert({
                        "lead_id": None,
                        "event_type": "handler_error",
                        "payload": {"lead_id": lead_id, "error": str(e), "messages": messages},
                    }).execute()
                except Exception:
                    pass
