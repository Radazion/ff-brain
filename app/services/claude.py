from anthropic import AsyncAnthropic
from app.config import ANTHROPIC_API_KEY

_client: AsyncAnthropic | None = None

def get_anthropic() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    return _client

async def chat(system_prompt: str, messages: list[dict], max_tokens: int = 1024) -> str:
    client = get_anthropic()
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text
