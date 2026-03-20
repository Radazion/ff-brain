import asyncio
import logging
from app.services import claude
from app.services.ghl import GHLClient
from app.models.lead import LeadModel
from app.models.conversation import ConversationModel
from app.orchestrator.window import should_use_template
from app.prompts.builder import get_config

logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(self):
        self.ghl = GHLClient()

    async def get_conversation_context(self, lead: dict) -> tuple[dict, list[dict]]:
        conv = ConversationModel.get_active(lead["id"])
        if not conv:
            conv = ConversationModel.create(lead["id"], self.agent_name)
        limit = get_config("context_messages", 20)
        messages = ConversationModel.get_recent_messages(conv["id"], limit=limit)
        claude_messages = []
        for msg in messages:
            role = "user" if msg["role"] == "lead" else "assistant"
            claude_messages.append({"role": role, "content": msg["content"]})
        return conv, claude_messages

    async def send_response(self, lead: dict, conv: dict, response_text: str):
        delays = get_config("timing_delays", {"first_response": 45, "between_messages": 30})
        await asyncio.sleep(delays.get("first_response", 45))
        chunks = self._split_message(response_text)
        for i, chunk in enumerate(chunks):
            if should_use_template(lead):
                logger.info(f"Window closed for {lead['id']}, skipping free-form message")
                return
            try:
                await self.ghl.send_message(lead["ghl_contact_id"], chunk)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                return
            ConversationModel.add_message(conv["id"], "bot", chunk)
            if i < len(chunks) - 1:
                await asyncio.sleep(delays.get("between_messages", 30))

    def _split_message(self, text: str) -> list[str]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            return [text]
        return paragraphs

    @property
    def agent_name(self) -> str:
        raise NotImplementedError
