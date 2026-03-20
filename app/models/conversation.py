from datetime import datetime, timezone
from app.services.supabase_client import get_supabase

class ConversationModel:
    TABLE = "conversations"
    MSG_TABLE = "messages"

    @classmethod
    def create(cls, lead_id: str, agent: str) -> dict:
        db = get_supabase()
        result = db.table(cls.TABLE).insert({
            "lead_id": lead_id,
            "agent": agent,
            "status": "active",
        }).execute()
        return result.data[0]

    @classmethod
    def get_active(cls, lead_id: str) -> dict | None:
        db = get_supabase()
        result = db.table(cls.TABLE).select("*").eq("lead_id", lead_id).eq("status", "active").execute()
        return result.data[0] if result.data else None

    @classmethod
    def close(cls, conversation_id: str, reason: str, lead_id: str = None) -> dict:
        db = get_supabase()
        result = db.table(cls.TABLE).update({
            "status": "closed",
            "closed_at": datetime.now(timezone.utc).isoformat(),
            "close_reason": reason,
        }).eq("id", conversation_id).execute()
        conv = result.data[0]
        if lead_id:
            cls._trigger_intel(conversation_id, lead_id)
        return conv

    @classmethod
    def _trigger_intel(cls, conversation_id: str, lead_id: str):
        import asyncio
        from app.agents.intel import IntelAgent
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(IntelAgent().analyze_conversation(conversation_id, lead_id))
        except Exception:
            pass

    @classmethod
    def add_message(cls, conversation_id: str, role: str, content: str,
                    was_audio: bool = False, audio_url: str | None = None,
                    template_used: str | None = None) -> dict:
        db = get_supabase()
        msg = db.table(cls.MSG_TABLE).insert({
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "was_audio": was_audio,
            "original_audio_url": audio_url,
            "template_used": template_used,
        }).execute()
        db.table(cls.TABLE).update({
            "last_message_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", conversation_id).execute()
        return msg.data[0]

    @classmethod
    def get_recent_messages(cls, conversation_id: str, limit: int = 20) -> list[dict]:
        db = get_supabase()
        result = db.table(cls.MSG_TABLE).select("*").eq(
            "conversation_id", conversation_id
        ).order("created_at", desc=True).limit(limit).execute()
        return list(reversed(result.data))
