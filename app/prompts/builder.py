from app.services.supabase_client import get_supabase

def get_config(key: str, default=None):
    db = get_supabase()
    result = db.table("bot_config").select("value").eq("key", key).execute()
    if result.data:
        return result.data[0]["value"]
    return default

def get_knowledge(category: str = None, avatar_segment: str = "general") -> list[dict]:
    db = get_supabase()
    query = db.table("knowledge_base").select("*").eq("active", True)
    if category:
        query = query.eq("category", category)
    result = query.execute()
    return [kb for kb in result.data
            if kb["avatar_segment"] in (avatar_segment, "general")]

def get_funnel_resources(funnel_stage: str = None) -> list[dict]:
    db = get_supabase()
    query = db.table("funnel_resources").select("*").eq("active", True)
    if funnel_stage:
        query = query.eq("funnel_stage", funnel_stage)
    return query.execute().data

def build_setter_prompt(lead: dict) -> str:
    base_prompt = get_config("setter_system_prompt", "")
    cases = get_knowledge("caso_exito")
    objection_responses = get_knowledge("objecion_respuesta")
    faqs = get_knowledge("faq")
    rules = get_knowledge("regla")
    resources = get_funnel_resources(lead.get("funnel_stage"))

    cases_text = "\n".join(f"- {c['title']}: {c['content']}" for c in cases)
    objections_text = "\n".join(f"- {o['title']}: {o['content']}" for o in objection_responses)
    faqs_text = "\n".join(f"- {f['title']}: {f['content']}" for f in faqs)
    rules_text = "\n".join(f"- {r['content']}" for r in rules)
    resources_text = "\n".join(f"- {r['name']} ({r['funnel_stage']}): {r['url']}" for r in resources)

    lead_profile = f"""PERFIL DEL LEAD:
- Nombre: {lead.get('name', 'Desconocido')}
- Fuente: {lead.get('source', 'desconocida')}
- Etapa funnel: {lead.get('funnel_stage', 'sin_vsl')}
- Tipo diabetes: {lead.get('diabetes_type', 'no informado')}
- Medicación: {lead.get('medication', 'no informada')}
- Años con diabetes: {lead.get('years_with_diabetes', 'no informado')}
- Score calificación: {lead.get('qualification_score', 0)}/10
- Envió análisis: {'Sí' if lead.get('clinical_data_sent') else 'No'}
- Data del form: {lead.get('form_data', 'No hay')}"""

    return f"""{base_prompt}

{lead_profile}

CASOS DE ÉXITO DISPONIBLES:
{cases_text}

RESPUESTAS A OBJECIONES:
{objections_text}

PREGUNTAS FRECUENTES:
{faqs_text}

REGLAS ESTRICTAS:
{rules_text}

RECURSOS PARA COMPARTIR (solo si el momento es apropiado):
{resources_text}"""

def build_post_agenda_prompt(lead: dict, appointment: dict) -> str:
    base_prompt = get_config("post_agenda_system_prompt", "")
    resources = get_funnel_resources()
    resources_text = "\n".join(f"- {r['name']}: {r['url']}" for r in resources)

    return f"""{base_prompt}

PERFIL DEL LEAD:
- Nombre: {lead.get('name', 'Desconocido')}
- Llamada agendada: {appointment.get('scheduled_at', 'No definida')}
- Link zoom: {appointment.get('zoom_link', 'No definido')}
- Estado: {appointment.get('show_status', 'pending')}
- Intentos de rescate: {appointment.get('rescue_attempts', 0)}

RECURSOS:
{resources_text}"""
