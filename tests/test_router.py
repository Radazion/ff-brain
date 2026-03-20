from app.orchestrator.router import route_event

def test_route_new_lead():
    lead = {"status": "nuevo", "assigned_agent": "setter"}
    assert route_event("inbound_message", lead) == "setter"

def test_route_calificacion():
    lead = {"status": "en_calificacion", "assigned_agent": "setter"}
    assert route_event("inbound_message", lead) == "setter"

def test_route_agendado():
    lead = {"status": "agendado", "assigned_agent": "post_agenda"}
    assert route_event("appointment_booked", lead) == "post_agenda"

def test_route_escalado():
    lead = {"status": "escalado", "assigned_agent": "human"}
    assert route_event("inbound_message", lead) is None

def test_route_human_outbound():
    lead = {"status": "en_calificacion", "assigned_agent": "setter"}
    assert route_event("human_outbound", lead) == "escalate"
