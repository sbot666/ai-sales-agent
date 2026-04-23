import json
import os
from pathlib import Path
import anthropic
from agents.state import AgentState, ScoredLead

PROMPT = (Path(__file__).parent.parent / "prompts" / "scorer.md").read_text()
THRESHOLD = int(os.environ.get("SCORE_MIN", 60))

def _score_lead(client: anthropic.Anthropic, lead: dict) -> dict:
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        system=[{"type": "text", "text": PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Score this lead:\n"
                    f"Name: {lead['first_name']} {lead['last_name']}\n"
                    f"Title: {lead['title']}\n"
                    f"Company: {lead['company']}\n"
                    f"Company size: {lead.get('company_size', 'unknown')}\n"
                    f"Email: {lead['email']}\n"
                    f"Source: {lead['source']}"
                ),
            }
        ],
    )
    return json.loads(msg.content[0].text)

async def scorer_node(state: AgentState) -> dict:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    scored: list[ScoredLead] = []

    for lead in state["raw_leads"]:
        try:
            result = _score_lead(client, lead)
            if result["score"] >= THRESHOLD:
                scored.append({**lead, **result, "enrichment": {}})
        except Exception:
            pass

    return {"scored_leads": scored}
