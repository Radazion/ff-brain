import json
import logging
from datetime import datetime, timezone, timedelta
from app.services import claude
from app.models.conversation import ConversationModel
from app.models.intel_models import IntelModels
from app.models.lead import LeadModel

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """Analizá esta conversación de WhatsApp entre un bot setter y un lead
de un programa de reversión de diabetes. Extraé la siguiente información en formato JSON:

{
  "objections": [
    {"text": "lo que dijo el lead", "category": "precio|tiempo|confianza|medico|pareja|otro", "resolved": true/false, "resolution": "qué respuesta funcionó o null"}
  ],
  "questions": [
    {"text": "pregunta del lead", "category": "protocolo|precio|duracion|resultados|logistica"}
  ],
  "engagement_score": 1-10,
  "buy_signals": ["frase 1", "frase 2"],
  "drop_reason": "razón si no avanzó, o null",
  "summary": "resumen de 1 línea"
}

Respondé SOLO con el JSON, sin texto adicional."""

WEEKLY_PROMPT = """Analizá estos datos de la semana y generá un reporte de inteligencia
para el equipo de marketing. Formato JSON:

{
  "top_objections": [{"category": "...", "count": N, "best_response": "..."}],
  "top_questions": [{"text": "...", "count": N}],
  "insights": ["insight 1", "insight 2"],
  "recommendations": ["recomendación 1", "recomendación 2"]
}

Respondé SOLO con el JSON."""

class IntelAgent:
    async def analyze_conversation(self, conversation_id: str, lead_id: str):
        messages = ConversationModel.get_recent_messages(conversation_id, limit=100)
        if not messages:
            return
        conv_text = "\n".join(
            f"{'BOT' if m['role'] == 'bot' else 'LEAD'}: {m['content']}"
            for m in messages
        )
        response = await claude.chat(
            ANALYSIS_PROMPT,
            [{"role": "user", "content": conv_text}],
            max_tokens=2048,
        )
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            logger.error(f"Intel failed to parse response for conv {conversation_id}")
            return
        for obj in data.get("objections", []):
            IntelModels.save_objection({
                "lead_id": lead_id,
                "conversation_id": conversation_id,
                "text": obj["text"],
                "category": obj.get("category", "otro"),
                "resolved": obj.get("resolved", False),
                "resolution_text": obj.get("resolution"),
            })
        for q in data.get("questions", []):
            IntelModels.save_question({
                "lead_id": lead_id,
                "conversation_id": conversation_id,
                "question_text": q["text"],
                "category": q.get("category"),
            })
        lead = LeadModel.get(lead_id)
        outcome_map = {
            "agendado": "agendado", "pre_llamada": "agendado",
            "cerrado": "agendado", "descartado": "descartado",
            "dormido": "dormido", "escalado": "escalado",
        }
        outcome = outcome_map.get(lead.get("status", ""), "descartado") if lead else "descartado"
        IntelModels.save_conversation_score({
            "lead_id": lead_id,
            "conversation_id": conversation_id,
            "engagement_score": data.get("engagement_score", 5),
            "message_count": len(messages),
            "outcome": outcome,
            "drop_reason": data.get("drop_reason"),
        })

    async def generate_weekly_report(self):
        now = datetime.now(timezone.utc)
        week_start = (now - timedelta(days=7)).isoformat()
        week_end = now.isoformat()
        scores = IntelModels.get_week_scores(week_start, week_end)
        conversations = IntelModels.get_week_conversations(week_start, week_end)
        if not scores and not conversations:
            return
        summary = json.dumps({
            "total_conversations": len(conversations),
            "scores": scores,
            "period": f"{week_start} to {week_end}",
        }, default=str)
        response = await claude.chat(
            WEEKLY_PROMPT,
            [{"role": "user", "content": summary}],
            max_tokens=2048,
        )
        try:
            report = json.loads(response)
        except json.JSONDecodeError:
            logger.error("Intel failed to parse weekly report")
            return
        total = len(conversations)
        qualified = sum(1 for s in scores if (s.get("qualification_score") or 0) >= 6)
        scheduled = sum(1 for s in scores if s.get("outcome") == "agendado")
        IntelModels.save_weekly_report({
            "week_start": (now - timedelta(days=7)).date().isoformat(),
            "week_end": now.date().isoformat(),
            "total_leads": total,
            "qualified": qualified,
            "scheduled": scheduled,
            "showed": 0,
            "top_objections": report.get("top_objections", []),
            "top_questions": report.get("top_questions", []),
            "insights": report.get("insights", []),
        })
        logger.info(f"Weekly report generated: {total} leads, {qualified} qualified")
