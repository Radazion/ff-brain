from fastapi import FastAPI, Request, HTTPException
from app.config import WEBHOOK_SECRET
from app.orchestrator.router import route_event
from app.orchestrator.debounce import Debouncer
from app.models.lead import LeadModel
from app.models.conversation import ConversationModel
from app.services.ghl import GHLClient
import logging

logger = logging.getLogger(__name__)
app = FastAPI(title="FF Brain")
ghl = GHLClient()

async def process_messages(lead_id: str, messages: list[str]):
    lead = LeadModel.get(lead_id)
    if not lead:
        return
    combined = "\n".join(messages)
    agent = route_event("inbound_message", lead)
    if agent == "setter":
        from app.agents.setter import SetterAgent
        await SetterAgent().process(lead, combined)
    elif agent == "post_agenda":
        from app.agents.post_agenda import PostAgendaAgent
        await PostAgendaAgent().process(lead, combined)

debouncer = Debouncer(delay_seconds=15.0, handler=process_messages)

@app.post("/webhooks/ghl")
async def ghl_webhook(request: Request):
    secret = request.headers.get("X-Webhook-Secret", "")
    if secret and secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    payload = await request.json()
    _log_event(payload)
    if GHLClient.is_human_message(payload):
        await handle_human_takeover(payload)
        return {"status": "human_takeover"}
    if payload.get("direction") != "inbound":
        return {"status": "ignored"}
    contact_id = payload.get("contactId")
    if not contact_id:
        return {"status": "no_contact"}
    lead = LeadModel.find_by_ghl_id(contact_id)
    if not lead:
        lead = LeadModel.create({
            "ghl_contact_id": contact_id,
            "name": payload.get("contactName", ""),
            "phone": payload.get("phone", ""),
            "source": "whatsapp_directo",
        })
    LeadModel.refresh_window(lead["id"])
    message_text = payload.get("body", "")
    if payload.get("contentType") == "audio":
        audio_url = payload.get("mediaUrl", "")
        if audio_url:
            try:
                from app.services import whisper
                audio_bytes = await ghl.download_audio(audio_url)
                message_text = await whisper.transcribe(audio_bytes)
            except Exception as e:
                logger.error(f"Audio transcription failed: {e}")
                message_text = "[Audio no transcribible]"
    if not message_text:
        return {"status": "empty_message"}
    conv = ConversationModel.get_active(lead["id"])
    if not conv:
        conv = ConversationModel.create(lead["id"], lead.get("assigned_agent", "setter"))
    ConversationModel.add_message(
        conv["id"], "lead", message_text,
        was_audio=payload.get("contentType") == "audio",
        audio_url=payload.get("mediaUrl"),
    )
    await debouncer.add(lead["id"], message_text)
    return {"status": "processing"}

@app.post("/webhooks/ghl/form")
async def ghl_form_webhook(request: Request):
    secret = request.headers.get("X-Webhook-Secret", "")
    if secret and secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    payload = await request.json()
    contact_id = payload.get("contactId")
    lead = LeadModel.find_by_ghl_id(contact_id)
    form_fields = {
        "ghl_contact_id": contact_id,
        "name": payload.get("contactName", ""),
        "phone": payload.get("phone", ""),
        "email": payload.get("email", ""),
        "source": "form",
        "funnel_stage": "lleno_form",
        "form_data": payload.get("formData", {}),
    }
    if lead:
        LeadModel.update(lead["id"], form_fields)
        lead = LeadModel.get(lead["id"])
    else:
        lead = LeadModel.create(form_fields)
    LeadModel.refresh_window(lead["id"])
    ConversationModel.create(lead["id"], "setter")
    from app.agents.setter import SetterAgent
    await SetterAgent().process(lead, "[FORM_COMPLETED]")
    return {"status": "ok"}

@app.post("/webhooks/ghl/appointment")
async def ghl_appointment_webhook(request: Request):
    secret = request.headers.get("X-Webhook-Secret", "")
    if secret and secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    payload = await request.json()
    _log_event(payload)
    contact_id = payload.get("contactId")
    lead = LeadModel.find_by_ghl_id(contact_id)
    if not lead:
        return {"status": "lead_not_found"}
    from app.models.appointment import AppointmentModel
    from app.agents.post_agenda import PostAgendaAgent
    appointment = AppointmentModel.create({
        "lead_id": lead["id"],
        "ghl_appointment_id": payload.get("appointmentId", ""),
        "scheduled_at": payload.get("startTime", ""),
        "zoom_link": payload.get("meetingLink", ""),
    })
    LeadModel.update(lead["id"], {
        "status": "agendado",
        "funnel_stage": "agendado",
        "assigned_agent": "post_agenda",
    })
    agent = PostAgendaAgent()
    await agent.send_confirmation(lead, appointment)
    return {"status": "ok"}

@app.post("/webhooks/ghl/tag")
async def ghl_tag_webhook(request: Request):
    secret = request.headers.get("X-Webhook-Secret", "")
    if secret and secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    payload = await request.json()
    _log_event(payload)
    tag = payload.get("tag", "")
    contact_id = payload.get("contactId")
    if tag == "bot_activo" and contact_id:
        lead = LeadModel.find_by_ghl_id(contact_id)
        if lead and lead["status"] == "escalado":
            LeadModel.update(lead["id"], {
                "status": "en_calificacion",
                "assigned_agent": "setter",
            })
            return {"status": "returned_to_bot"}
    return {"status": "ignored"}

async def handle_human_takeover(payload: dict):
    contact_id = payload.get("contactId")
    lead = LeadModel.find_by_ghl_id(contact_id)
    if lead:
        LeadModel.update(lead["id"], {
            "assigned_agent": "human",
            "status": "escalado",
        })
        conv = ConversationModel.get_active(lead["id"])
        if conv:
            ConversationModel.close(conv["id"], "escalated_to_human", lead_id=lead["id"])

def _log_event(payload: dict):
    from app.services.supabase_client import get_supabase
    try:
        get_supabase().table("event_log").insert({
            "lead_id": None,
            "event_type": "webhook_received",
            "payload": payload,
        }).execute()
    except Exception:
        pass

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2026-03-30"}
