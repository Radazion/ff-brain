from app.services.supabase_client import get_supabase

class AppointmentModel:
    TABLE = "appointments"

    @classmethod
    def create(cls, data: dict) -> dict:
        db = get_supabase()
        return db.table(cls.TABLE).insert(data).execute().data[0]

    @classmethod
    def get_by_lead(cls, lead_id: str) -> dict | None:
        db = get_supabase()
        result = db.table(cls.TABLE).select("*").eq("lead_id", lead_id).order(
            "created_at", desc=True
        ).limit(1).execute()
        return result.data[0] if result.data else None

    @classmethod
    def update(cls, appointment_id: str, data: dict) -> dict:
        db = get_supabase()
        return db.table(cls.TABLE).update(data).eq("id", appointment_id).execute().data[0]

    @classmethod
    def get_pending_reminders(cls) -> list[dict]:
        db = get_supabase()
        return db.table(cls.TABLE).select("*, leads(*)").eq(
            "show_status", "pending"
        ).execute().data
