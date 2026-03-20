"""Seed Supabase with initial configuration and knowledge base."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.services.supabase_client import get_supabase

db = get_supabase()

# BOT CONFIG
configs = [
    {
        "key": "setter_system_prompt",
        "value": "Sos un asistente del equipo de Revertir la Diabetes. Tu rol es conversar con personas que tienen diabetes tipo 2 o prediabetes y están buscando una solución.\n\nPERSONALIDAD:\n- Hablás en argentino natural (vos, tenés, dale)\n- Mensajes CORTOS: 1-3 líneas máximo por mensaje\n- Empático, cercano, pero profesional\n- NUNCA das consejos médicos. Siempre: \"eso lo evalúa el especialista en tu sesión\"\n- NUNCA mencionás el nombre \"Fran\". Siempre decís \"un especialista\" o \"el equipo\"\n- NUNCA das el precio exacto. Reframeás como inversión recuperable en ahorro de medicación\n- Te presentás como \"del equipo de Revertir la Diabetes\"\n\nOBJETIVO:\n1. Entender la situación del lead (tipo diabetes, medicación, hace cuánto, motivación)\n2. Nutrir con un caso de éxito relevante\n3. Calificar (score 1-10)\n4. Si califica → entregar link del calendario\n5. Si no califica → cerrar con elegancia\n\nACCIONES DISPONIBLES (incluí en tu respuesta cuando corresponda):\n[ACTION:update_score:+N:razón] — sumar N puntos al score\n[ACTION:update_field:nombre_campo:valor] — actualizar dato del lead\n[ACTION:share_resource:nombre_recurso] — compartir un recurso\n[ACTION:deliver_calendar] — entregar el calendario (solo si score >= 6)\n\nMANEJO DE OBJECIONES (framework AAA):\n1. Acknowledge: \"Te entiendo, es lógico pensarlo así\"\n2. Associate: contar caso similar\n3. Ask: pregunta que retome el control\n\nREGLA DE PRECIO:\nCuando pregunten cuánto sale:\n\"El protocolo tiene un costo que se ajusta a cada caso. Lo que te puedo decir es que la mayoría de los pacientes recuperan la inversión en pocos meses solo en ahorro de medicación. ¿Cuánto estás gastando hoy por mes en medicamentos?\"\n\nNUNCA:\n- Inventar casos o números\n- Dar diagnósticos o consejos médicos\n- Prometer resultados específicos\n- Mandar mensajes largos (máx 3 líneas por burbuja)\n- Usar emojis en exceso (máx 1 por mensaje, y no siempre)",
        "description": "System prompt principal del Setter"
    },
    {
        "key": "post_agenda_system_prompt",
        "value": "Sos del equipo de Revertir la Diabetes. El lead ya agendó una sesión con un especialista. Tu rol es prepararlo para que llegue entusiasmado y listo.\n\nPERSONALIDAD: Misma que el setter (argentino, corto, empático).\n\nOBJETIVO: Que el lead se presente a la llamada preparado, con sus análisis, y emocionado.\n\nNUNCA: Consejos médicos, nombre de Fran, precio exacto.",
        "description": "System prompt del Post-Agenda"
    },
    {
        "key": "timing_delays",
        "value": {"first_response": 45, "between_messages": 30},
        "description": "Segundos de delay para parecer humano"
    },
    {
        "key": "followup_hours",
        "value": {"first": 4, "second": 24, "archive": 72},
        "description": "Horas para follow-ups del Setter"
    },
    {
        "key": "qualification_threshold",
        "value": 6,
        "description": "Score mínimo para entregar calendario"
    },
    {
        "key": "max_rescue_attempts",
        "value": 2,
        "description": "Intentos máximos de rescate no-show"
    },
    {
        "key": "context_messages",
        "value": 20,
        "description": "Mensajes de contexto para Claude"
    },
]

for config in configs:
    db.table("bot_config").upsert(config, on_conflict="key").execute()
print(f"✓ {len(configs)} configs cargadas")

# KNOWLEDGE BASE
knowledge = [
    {
        "category": "caso_exito",
        "title": "Caso Verónica — dejó la insulina en 60 días",
        "content": "Verónica tenía diabetes tipo 2 hace 8 años, se inyectaba insulina todos los días. Siguió el protocolo y en 60 días dejó la insulina por completo. Su médico no lo podía creer.",
        "avatar_segment": "general",
        "priority": 1,
    },
    {
        "category": "caso_exito",
        "title": "Caso Guillermina — dejó la metformina",
        "content": "Guillermina era prediabética, tomaba metformina. En 45 días normalizó sus valores y su médico le sacó la medicación.",
        "avatar_segment": "general",
        "priority": 2,
    },
    {
        "category": "caso_exito",
        "title": "Caso Mario — 30 a 7 unidades en 13 días",
        "content": "Mario se inyectaba 30 unidades de insulina por día hace 30 años. En 13 días bajó a 7 unidades y tuvo hipoglucemia — necesitaba aún menos.",
        "avatar_segment": "general",
        "priority": 3,
    },
    {
        "category": "objecion_respuesta",
        "title": "Objeción precio",
        "content": "Reframear: '¿Cuánto gastás por mes en medicación? Eso son X al año. El protocolo es una inversión única que la mayoría recupera en meses solo en ahorro de medicamentos.'",
        "avatar_segment": "general",
        "priority": 1,
    },
    {
        "category": "objecion_respuesta",
        "title": "Objeción 'tengo que consultarlo'",
        "content": "Validar: 'Totalmente, es una decisión importante. ¿Querés que esté presente esa persona en la sesión con el especialista? Así pueden decidir juntos con toda la info.'",
        "avatar_segment": "general",
        "priority": 2,
    },
    {
        "category": "objecion_respuesta",
        "title": "Objeción 'mi médico dice que no se puede'",
        "content": "Reframear: 'Tu médico gestiona la diabetes, que es distinto a revertirla. Son enfoques complementarios. El protocolo trabaja CON tu médico, no en contra.'",
        "avatar_segment": "general",
        "priority": 3,
    },
    {
        "category": "faq",
        "title": "¿Cuánto dura el protocolo?",
        "content": "El protocolo base es de 30 días. Muchos pacientes ven cambios en los primeros días. El especialista te da el plan exacto en la sesión.",
        "avatar_segment": "general",
        "priority": 1,
    },
    {
        "category": "faq",
        "title": "¿Funciona para mi tipo de diabetes?",
        "content": "El protocolo está diseñado para diabetes tipo 2 y prediabetes. Cada caso es distinto, por eso el especialista analiza TU caso específico en la sesión.",
        "avatar_segment": "general",
        "priority": 2,
    },
    {
        "category": "regla",
        "title": "No dar consejos médicos",
        "content": "NUNCA des consejos médicos, diagnósticos ni recomendaciones de medicación. Siempre derivá al especialista: 'Eso lo evalúa el especialista en tu sesión.'",
        "avatar_segment": "general",
        "priority": 0,
    },
    {
        "category": "regla",
        "title": "No mencionar a Fran",
        "content": "NUNCA mencionés el nombre 'Fran' ni 'Francisco'. Siempre decí 'un especialista', 'el especialista', 'nuestro equipo', 'el equipo de Revertir la Diabetes'.",
        "avatar_segment": "general",
        "priority": 0,
    },
]

for kb in knowledge:
    db.table("knowledge_base").insert(kb).execute()
print(f"✓ {len(knowledge)} entradas de knowledge base cargadas")

# FUNNEL RESOURCES
resources = [
    {
        "name": "Landing + VSL",
        "type": "link",
        "url": "https://ACTUALIZAR-CON-URL-REAL.com",
        "funnel_stage": "sin_vsl",
        "avatar_segment": "general",
        "description": "Enviar cuando el lead no vio el VSL",
    },
    {
        "name": "Formulario",
        "type": "link",
        "url": "https://ACTUALIZAR-CON-URL-REAL.com/form",
        "funnel_stage": "vio_vsl",
        "avatar_segment": "general",
        "description": "Enviar cuando vio VSL pero no llenó form",
    },
    {
        "name": "Página del protocolo",
        "type": "link",
        "url": "https://ACTUALIZAR-CON-URL-REAL.com/protocolo",
        "funnel_stage": "calificado",
        "avatar_segment": "general",
        "description": "Enviar post-agenda para que el lead se prepare",
    },
    {
        "name": "Calendario",
        "type": "link",
        "url": "https://ACTUALIZAR-CON-URL-REAL.com/calendario",
        "funnel_stage": "calificado",
        "avatar_segment": "general",
        "description": "SOLO entregar cuando el lead está calificado (score >= 6)",
    },
]

for res in resources:
    db.table("funnel_resources").insert(res).execute()
print(f"✓ {len(resources)} recursos de funnel cargados")

print("\n✅ Seed completo. Actualizar las URLs reales en funnel_resources.")
