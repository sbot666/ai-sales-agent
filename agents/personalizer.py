import json
import os
from pathlib import Path
import anthropic
import yaml
from agents.state import AgentState, EmailDraft

PROMPT = (Path(__file__).parent.parent / "prompts" / "personalizer.md").read_text()

def _personalize(client: anthropic.Anthropic, lead: dict, template: dict) -> dict:
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=[{"type": "text", "text": PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Write a cold email for:\n"
                    f"Name: {lead['first_name']} {lead['last_name']}\n"
                    f"Title: {lead['title']}\n"
                    f"Company: {lead['company']} ({lead.get('company_size', '?')} employees)\n"
                    f"Email: {lead['email']}\n"
                    f"Sequence goal: {template['goal']}\n"
                    f"CTA: {template['cta']}\n"
                    f"Scoring reasoning: {lead.get('reasoning', '')}"
                ),
            }
        ],
    )
    return json.loads(msg.content[0].text)

async def personalizer_node(state: AgentState) -> dict:
    cfg = state["run_config"]
    template_name = cfg.get("sequence_template", "demo-book")
    sequences_dir = Path(__file__).parent.parent / "config" / "sequences"

    with open(sequences_dir / f"{template_name}.yaml") as f:
        template = yaml.safe_load(f)

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    drafts: list[EmailDraft] = []

    for lead in state["scored_leads"]:
        try:
            result = _personalize(client, lead, template)
            drafts.append(EmailDraft(
                email=lead["email"],
                first_name=lead["first_name"],
                company=lead["company"],
                subject_a=result["subject_a"],
                subject_b=result["subject_b"],
                body=result["body"],
                template_name=template_name,
            ))
        except Exception:
            pass

    return {"email_drafts": drafts, "awaiting_approval": True}
