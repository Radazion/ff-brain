import logging
from app.agents.base import BaseAgent
from app.services import claude
from app.services.ghl import GHLClient
from app.models.lead import LeadModel
from app.models.conversation import ConversationModel
from app.models.appointment import AppointmentModel
from app.prompts.builder import build_post_agenda_prompt, get_config
from app.orchestrator.window import should_use_template

logger = logging.getLogger(__name__)

class PostAgendaAgent(BaseAgent):
    @property
    def agent_name(self) -> str:
        return "post_agenda"

    async def process(self, lead: dict, message: str):
        appointment = AppointmentModel.get_by_lead(lead["id"])
        if not appointment:
            return
        conv, claude_messages = await self.get_conversation_context(lead)
        claude_messages.append({"role": "user", "content": message})
        system_prompt = build_post_agenda_prompt(lead, appointment)
        response = await claude.chat(system_prompt, claude_messages)
        await self.send_response(lead, conv, response)

    async def send_confirmation(self, lead: dict, appointment: dict):
        conv = ConversationModel.get_active(lead["id"])
        if not conv:
            conv = ConversationModel.create(lead["id"], "post_agenda")
        if not should_use_template(lead):
            system_prompt = build_post_agenda_prompt(lead, appointment)
            msg = await claude.chat(system_prompt, [{
                "role": "user",
                "content": "[SYSTEM: El lead acaba de agendar. Mandá confirmación con link a la página del protocolo.]"
            }])
            await self.send_response(lead, conv, msg)
        else:
            ghl = GHLClient()
            await ghl.send_template(lead["ghl_contact_id"], "confirmacion_agenda", {
                "name": lead.get("name", ""),
                "fecha": appointment.get("scheduled_at", ""),
            })

    async def send_reminder_24h(self, appointment: dict):
        lead = LeadModel.get(appointment["lead_id"])
        if not lead:
            return
        ghl = GHLClient()
        await ghl.send_template(lead["ghl_contact_id"], "reminder_24h", {
            "name": lead.get("name", ""),
            "hora": appointment.get("scheduled_at", ""),
        })
        LeadModel.update_status(lead["id"], "pre_llamada")

    async def send_reminder_2h(self, appointment: dict):
        lead = LeadModel.get(appointment["lead_id"])
        if not lead:
            return
        ghl = GHLClient()
        await ghl.send_template(lead["ghl_contact_id"], "reminder_2h", {
            "name": lead.get("name", ""),
            "link": appointment.get("zoom_link", ""),
        })

    async def handle_noshow(self, appointment: dict):
        lead = LeadModel.get(appointment["lead_id"])
        if not lead:
            return
        attempts = appointment.get("rescue_attempts", 0)
        max_attempts = get_config("max_rescue_attempts", 2)
        if attempts >= max_attempts:
            LeadModel.update_status(lead["id"], "dormido")
            return
        ghl = GHLClient()
        template = "rescate_noshow" if attempts == 0 else "rescate_noshow_final"
        await ghl.send_template(lead["ghl_contact_id"], template, {
            "name": lead.get("name", ""),
        })
        AppointmentModel.update(appointment["id"], {
            "rescue_attempts": attempts + 1,
        })
        LeadModel.update_status(lead["id"], "post_llamada")
