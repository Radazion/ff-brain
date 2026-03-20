def route_event(event_type: str, lead: dict) -> str | None:
    if event_type == "human_outbound":
        return "escalate"
    if lead.get("assigned_agent") == "human" or lead.get("status") == "escalado":
        return None
    status = lead.get("status", "nuevo")
    if event_type in ("appointment_booked", "appointment_noshow"):
        return "post_agenda"
    if event_type in ("tag_venta_cerrada", "tag_no_cerro", "tag_pensando"):
        return "post_agenda"
    if event_type == "conversation_closed":
        return "intel"
    if event_type == "inbound_message":
        if status in ("nuevo", "en_calificacion", "calificado", "dormido", "descartado"):
            return "setter"
        if status in ("agendado", "pre_llamada", "post_llamada"):
            return "post_agenda"
    return None
