import json
import os
from pathlib import Path
import anthropic
from agents.state import AgentState
from tools.sendgrid import send_email
from tools.calendly import get_scheduling_link

PROMPT = (Path(__file__).parent.parent / "prompts" / "follow_up.md").read_text()

OBJECTION_RESPONSES = {
    "price": "I understand budget is a concern. Many customers felt the same way before seeing the ROI — on average they recoup the cost in 6 weeks. Would it help to walk through an ROI estimate for {company}?",
    "timing": "Completely understand — bad timing is real. Would it make sense to reconnect in 30 days? I'll send a quick note then.",
    "competitor": "Fair enough — always good to evaluate options. One thing our customers highlight vs alternatives is [key differentiator]. Would a 20-min comparison call be useful?",
    "no_authority": "Thanks for the transparency — would you be able to point me to the right person? I want to make sure I'm not wasting anyone's time.",
    "no_need": "Appreciate the honesty. Out of curiosity, what does your current process look like for [problem domain]? Always learning.",
    "other": "Thanks for the context. Let me think about how we can best help — I'll follow up with something specific.",
}

async def follow_up_node(state: AgentState) -> dict:
    cfg = state["run_config"]
    reply = state.get("reply_event", {})
    email = reply.get("email", "")
    content = reply.get("content", "")

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

    classify_msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        system=[{"type": "text", "text": PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": f"Classify this reply:\n\n{content}"}],
    )
    classification = json.loads(classify_msg.content[0].text)
    sentiment = classification["sentiment"]

    if sentiment == "interested":
        link = await get_scheduling_link(
            cfg.get("calendly_api_key", os.environ.get("CALENDLY_API_KEY", "")),
            cfg.get("calendly_event_url", os.environ.get("CALENDLY_EVENT_URL", "")),
            email,
        )
        await send_email(
            api_key=cfg.get("sendgrid_api_key", os.environ.get("SENDGRID_API_KEY", "")),
            from_email=cfg.get("from_email", os.environ.get("SENDGRID_FROM_EMAIL", "")),
            to_email=email,
            subject="Here's a link to book time",
            body=f"Great to hear! Here's a link to grab time:\n\n{link}\n\nLooking forward to it.",
        )
        return {"follow_up_action": "calendly_sent", "errors": []}

    elif sentiment == "objection":
        objection_type = classification.get("objection_type", "other")
        template = OBJECTION_RESPONSES.get(objection_type, OBJECTION_RESPONSES["other"])
        response_msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=256,
            messages=[{"role": "user", "content": f"Expand this into a short natural email reply (2-3 sentences):\n{template}"}],
        )
        await send_email(
            api_key=cfg.get("sendgrid_api_key", os.environ.get("SENDGRID_API_KEY", "")),
            from_email=cfg.get("from_email", os.environ.get("SENDGRID_FROM_EMAIL", "")),
            to_email=email,
            subject="Re: your note",
            body=response_msg.content[0].text,
        )
        return {"follow_up_action": "objection_handled", "errors": []}

    elif sentiment == "not_interested":
        return {"follow_up_action": "unsubscribed", "errors": []}

    return {"follow_up_action": "neutral_ignored", "errors": []}
