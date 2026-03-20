from datetime import datetime, timezone

def is_window_open(lead: dict) -> bool:
    window_until = lead.get("window_open_until")
    if not window_until:
        return False
    if isinstance(window_until, str):
        window_until = datetime.fromisoformat(window_until)
    return datetime.now(timezone.utc) < window_until

def should_use_template(lead: dict) -> bool:
    return not is_window_open(lead)
