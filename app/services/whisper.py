from openai import AsyncOpenAI
from app.config import OPENAI_API_KEY
import tempfile
import os

_client: AsyncOpenAI | None = None

def get_openai() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _client

async def transcribe(audio_bytes: bytes, filename: str = "audio.ogg") -> str:
    client = get_openai()
    with tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[1], delete=False) as f:
        f.write(audio_bytes)
        f.flush()
        tmp_path = f.name
    try:
        with open(tmp_path, "rb") as audio_file:
            result = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="es",
            )
        return result.text
    finally:
        os.unlink(tmp_path)
