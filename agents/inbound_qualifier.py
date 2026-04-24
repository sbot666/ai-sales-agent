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

    # Inject system prompt as opening exchange (proxy compatibility)
    prefixed_messages = [
        {"role": "user", "content": f"<instructions>\n{system_prompt}\n</instructions>"},
        {"role": "assistant", "content": "Understood. I am a B2B SaaS sales qualification specialist. I will conduct BANT qualification and respond ONLY with valid JSON as specified."},
        *messages,
    ]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=prefixed_messages,
    )

    raw_text = response.content[0].text.strip()
    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        result = {"qualified": None, "next_message": raw_text}
    return {"inbound_result": result}
