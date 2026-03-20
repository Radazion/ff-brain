from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta, timezone
from app.services.supabase_client import get_supabase
import logging

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

def init_scheduler():
    scheduler.add_job(
        check_reminders,
        "interval",
        minutes=5,
        id="check_reminders",
        replace_existing=True,
    )
    scheduler.add_job(
        check_followups,
        "interval",
        minutes=15,
        id="check_followups",
        replace_existing=True,
    )
    scheduler.add_job(
        run_intel_weekly,
        CronTrigger(day_of_week="mon", hour=11, minute=0),
        id="intel_weekly",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started")

async def check_reminders():
    from app.models.appointment import AppointmentModel
    from app.agents.post_agenda import PostAgendaAgent
    appointments = AppointmentModel.get_pending_reminders()
    now = datetime.now(timezone.utc)
    agent = PostAgendaAgent()
    for apt in appointments:
        scheduled = datetime.fromisoformat(apt["scheduled_at"])
        hours_until = (scheduled - now).total_seconds() / 3600
        if 23 <= hours_until <= 25 and not apt["reminder_24h_sent"]:
            await agent.send_reminder_24h(apt)
            AppointmentModel.update(apt["id"], {"reminder_24h_sent": True})
        elif 1.5 <= hours_until <= 2.5 and not apt["reminder_2h_sent"]:
            await agent.send_reminder_2h(apt)
            AppointmentModel.update(apt["id"], {"reminder_2h_sent": True})
        elif hours_until < -1 and apt["show_status"] == "pending":
            AppointmentModel.update(apt["id"], {"show_status": "no_show"})
            await agent.handle_noshow(apt)

async def check_followups():
    from app.models.conversation import ConversationModel
    from app.agents.setter import SetterAgent
    from app.models.lead import LeadModel
    from app.prompts.builder import get_config
    db = get_supabase()
    followup_config = get_config("followup_hours", {"first": 4, "second": 24, "archive": 72})
    now = datetime.now(timezone.utc)
    convos = db.table("conversations").select(
        "*, leads(*)"
    ).eq("status", "active").eq("agent", "setter").execute().data
    setter = SetterAgent()
    for conv in convos:
        if not conv.get("last_message_at"):
            continue
        last_msg = datetime.fromisoformat(conv["last_message_at"])
        hours_since = (now - last_msg).total_seconds() / 3600
        lead = conv.get("leads", {})
        if not lead or lead.get("assigned_agent") == "human":
            continue
        msgs = ConversationModel.get_recent_messages(conv["id"], limit=1)
        if msgs and msgs[-1]["role"] == "bot":
            if hours_since >= followup_config["archive"]:
                LeadModel.update_status(lead["id"], "dormido")
                ConversationModel.close(conv["id"], "archived_no_response")
            elif hours_since >= followup_config["second"]:
                from app.services.ghl import GHLClient
                ghl_client = GHLClient()
                await ghl_client.send_template(
                    lead["ghl_contact_id"], "followup_24h",
                    {"name": lead.get("name", "")},
                )
            elif hours_since >= followup_config["first"]:
                await setter.process(lead, "[SYSTEM: El lead no respondió en 4+ horas. Hacé un follow-up corto y natural.]")

async def run_intel_weekly():
    from app.agents.intel import IntelAgent
    agent = IntelAgent()
    await agent.generate_weekly_report()
