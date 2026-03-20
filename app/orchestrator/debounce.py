import asyncio
from typing import Callable, Awaitable

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
            await self.handler(lead_id, messages)
