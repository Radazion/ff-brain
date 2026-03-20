from app.services.supabase_client import get_supabase

class IntelModels:
    @classmethod
    def save_objection(cls, data: dict) -> dict:
        db = get_supabase()
        return db.table("objections").insert(data).execute().data[0]

    @classmethod
    def save_question(cls, data: dict) -> dict:
        db = get_supabase()
        return db.table("frequent_questions").insert(data).execute().data[0]

    @classmethod
    def save_conversation_score(cls, data: dict) -> dict:
        db = get_supabase()
        return db.table("conversation_scores").insert(data).execute().data[0]

    @classmethod
    def save_weekly_report(cls, data: dict) -> dict:
        db = get_supabase()
        return db.table("weekly_reports").insert(data).execute().data[0]

    @classmethod
    def get_week_conversations(cls, week_start: str, week_end: str) -> list[dict]:
        db = get_supabase()
        return db.table("conversations").select(
            "*, messages(*), leads(*)"
        ).gte("started_at", week_start).lte("started_at", week_end).execute().data

    @classmethod
    def get_week_scores(cls, week_start: str, week_end: str) -> list[dict]:
        db = get_supabase()
        return db.table("conversation_scores").select("*").gte(
            "created_at", week_start
        ).lte("created_at", week_end).execute().data
