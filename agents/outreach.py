import os
from agents.state import AgentState
from tools.sendgrid import send_email

async def outreach_node(state: AgentState) -> dict:
    cfg = state["run_config"]
    api_key = cfg.get("sendgrid_api_key", os.environ.get("SENDGRID_API_KEY", ""))
    from_email = cfg.get("from_email", os.environ.get("SENDGRID_FROM_EMAIL", ""))
    errors = []

    for draft in state.get("approved_drafts", []):
        try:
            await send_email(
                api_key=api_key,
                from_email=from_email,
                to_email=draft["email"],
                subject=draft["subject_a"],
                body=draft["body"],
                tracking_settings={
                    "click_tracking": {"enable": True},
                    "open_tracking": {"enable": True},
                },
            )
        except Exception as e:
            errors.append(f"Failed to send to {draft['email']}: {e}")

    return {"errors": errors}
