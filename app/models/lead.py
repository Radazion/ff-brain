from datetime import datetime, timezone, timedelta
from app.services.supabase_client import get_supabase

class LeadModel:
    TABLE = "leads"

    @classmethod
    def create(cls, data: dict) -> dict:
        db = get_supabase()
        result = db.table(cls.TABLE).insert(data).execute()
        return result.data[0]

    @classmethod
    def find_by_phone(cls, phone: str) -> dict | None:
        db = get_supabase()
        result = db.table(cls.TABLE).select("*").eq("phone", phone).execute()
        return result.data[0] if result.data else None

    @classmethod
    def find_by_ghl_id(cls, ghl_contact_id: str) -> dict | None:
        db = get_supabase()
        result = db.table(cls.TABLE).select("*").eq("ghl_contact_id", ghl_contact_id).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get(cls, lead_id: str) -> dict | None:
        db = get_supabase()
        result = db.table(cls.TABLE).select("*").eq("id", lead_id).execute()
        return result.data[0] if result.data else None

    @classmethod
    def update_status(cls, lead_id: str, status: str) -> dict:
        db = get_supabase()
        result = db.table(cls.TABLE).update({"status": status}).eq("id", lead_id).execute()
        return result.data[0]

    @classmethod
    def update(cls, lead_id: str, data: dict) -> dict:
        db = get_supabase()
        result = db.table(cls.TABLE).update(data).eq("id", lead_id).execute()
        return result.data[0]

    @classmethod
    def refresh_window(cls, lead_id: str) -> dict:
        window = datetime.now(timezone.utc) + timedelta(hours=24)
        return cls.update(lead_id, {"window_open_until": window.isoformat()})

    @classmethod
    def is_window_open(cls, lead: dict) -> bool:
        if not lead.get("window_open_until"):
            return False
        window = datetime.fromisoformat(lead["window_open_until"])
        return datetime.now(timezone.utc) < window
