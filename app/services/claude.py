from google import genai
from app.config import GOOGLE_API_KEY

_client: genai.Client | None = None

def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client

async def chat(system_prompt: str, messages: list[dict], max_tokens: int = 1024) -> str:
    client = get_client()
    # Convert Claude-format messages to Gemini contents
    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(genai.types.Content(
            role=role,
            parts=[genai.types.Part(text=msg["content"])],
        ))
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text
