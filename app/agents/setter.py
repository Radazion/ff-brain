import json
import logging
from app.agents.base import BaseAgent
from app.services import claude
from app.models.lead import LeadModel
from app.models.conversation import ConversationModel
from app.prompts.builder import build_setter_prompt, get_config, get_funnel_resources

logger = logging.getLogger(__name__)

ESCALATION_KEYWORDS = [
    "hablar con alguien", "hablar con una persona", "quiero hablar",
    "llamame", "necesito un humano", "agente",
]

class SetterAgent(BaseAgent):
    @property
    def agent_name(self) -> str:
        return "setter"

    async def process(self, lead: dict, message: str):
        if lead["status"] in ("nuevo", "dormido", "descartado"):
            LeadModel.update_status(lead["id"], "en_calificacion")
            lead["status"] = "en_calificacion"
        if self._should_escalate(message):
            await self._escalate(lead)
            return
        conv, claude_messages = await self.get_conversation_context(lead)
        if message != "[FORM_COMPLETED]":
            claude_messages.append({"role": "user", "content": message})
        else:
            claude_messages.append({
                "role": "user",
                "content": "[SYSTEM: El lead acaba de completar el formulario. Iniciá la conversación.]"
            })
        system_prompt = build_setter_prompt(lead)
        response = await claude.chat(system_prompt, claude_messages)
        response, actions = self._parse_actions(response)
        await self._execute_actions(lead, actions)
        await self.send_response(lead, conv, response)

    def _should_escalate(self, message: str) -> bool:
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in ESCALATION_KEYWORDS)

    async def _escalate(self, lead: dict):
        from app.services.ghl import GHLClient
        ghl = GHLClient()
        LeadModel.update(lead["id"], {
            "status": "escalado",
            "assigned_agent": "human",
        })
        await ghl.add_tag(lead["ghl_contact_id"], "escalado_bot")
        conv = ConversationModel.get_active(lead["id"])
        if conv:
            ConversationModel.add_message(
                conv["id"], "system", "Lead escalado a humano por pedido"
            )

    def _parse_actions(self, response: str) -> tuple[str, list[dict]]:
        actions = []
        clean_lines = []
        for line in response.split("\n"):
            if line.strip().startswith("[ACTION:"):
                action_str = line.strip()[8:-1]
                parts = action_str.split(":")
                actions.append({"type": parts[0], "params": parts[1:]})
            else:
                clean_lines.append(line)
        return "\n".join(clean_lines).strip(), actions

    async def _execute_actions(self, lead: dict, actions: list[dict]):
        for action in actions:
            try:
                if action["type"] == "update_score":
                    delta = int(action["params"][0])
                    new_score = (lead.get("qualification_score") or 0) + delta
                    LeadModel.update(lead["id"], {"qualification_score": new_score})
                    lead["qualification_score"] = new_score
                elif action["type"] == "update_field":
                    field = action["params"][0]
                    value = action["params"][1]
                    if value == "true":
                        value = True
                    elif value == "false":
                        value = False
                    LeadModel.update(lead["id"], {field: value})
                elif action["type"] == "deliver_calendar":
                    threshold = get_config("qualification_threshold", 6)
                    if (lead.get("qualification_score") or 0) >= threshold:
                        LeadModel.update(lead["id"], {
                            "status": "calificado",
                            "funnel_stage": "calificado",
                        })
                elif action["type"] == "share_resource":
                    pass
            except Exception as e:
                logger.error(f"Action failed: {action}, error: {e}")
