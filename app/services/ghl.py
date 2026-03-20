import httpx
from app.config import GHL_API_TOKEN, GHL_BASE_URL, GHL_API_VERSION, GHL_LOCATION_ID

class GHLClient:
    def __init__(self):
        self.http = httpx.AsyncClient(
            base_url=GHL_BASE_URL,
            headers={
                "Authorization": f"Bearer {GHL_API_TOKEN}",
                "Version": GHL_API_VERSION,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def send_message(self, contact_id: str, message: str) -> dict:
        response = await self.http.post(
            "/conversations/messages",
            json={"type": "WhatsApp", "contactId": contact_id, "message": message},
        )
        response.raise_for_status()
        return response.json()

    async def send_template(self, contact_id: str, template_name: str, variables: dict) -> dict:
        response = await self.http.post(
            "/conversations/messages",
            json={
                "type": "WhatsApp",
                "contactId": contact_id,
                "templateName": template_name,
                "templateVariables": variables,
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_contact(self, contact_id: str) -> dict:
        response = await self.http.get(f"/contacts/{contact_id}")
        response.raise_for_status()
        return response.json().get("contact", response.json())

    async def add_tag(self, contact_id: str, tag: str) -> dict:
        response = await self.http.post(
            f"/contacts/{contact_id}/tags",
            json={"tags": [tag]},
        )
        response.raise_for_status()
        return response.json()

    async def download_audio(self, audio_url: str) -> bytes:
        response = await self.http.get(audio_url)
        response.raise_for_status()
        return response.content

    @staticmethod
    def is_human_message(webhook_payload: dict) -> bool:
        return (
            webhook_payload.get("direction") == "outbound"
            and webhook_payload.get("type") == "manual"
        )
