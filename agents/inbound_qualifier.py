import json
import os
from pathlib import Path
import anthropic

PROMPT = (Path(__file__).parent.parent / "prompts" / "inbound_qualifier.md").read_text()

async def inbound_qualifier_node(state: dict) -> dict:
    cfg = state.get("run_config", {})
    conversation = state.get("inbound_conversation", {})
    messages = conversation.get("messages", [])
    email = conversation.get("email", "")
    calendly_url = cfg.get("calendly_event_url", os.environ.get("CALENDLY_EVENT_URL", ""))

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    system_prompt = PROMPT.replace("[calendly_link]", f"{calendly_url}?email={email}")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
        messages=messages,
    )

    result = json.loads(response.content[0].text)
    return {"inbound_result": result}
