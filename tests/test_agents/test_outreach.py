import pytest
from unittest.mock import AsyncMock, patch
from agents.state import make_initial_state
from agents.outreach import outreach_node

async def test_outreach_sends_approved_drafts():
    drafts = [
        {"email": "ceo@acme.io", "first_name": "Jane", "company": "Acme",
         "subject_a": "Quick Q", "subject_b": "Value prop",
         "body": "Hi Jane", "template_name": "demo-book"},
    ]
    state = make_initial_state(run_config={"sendgrid_api_key": "SG.fake", "from_email": "out@co.io"})
    state["approved_drafts"] = drafts
    state["awaiting_approval"] = False

    with patch("agents.outreach.send_email", AsyncMock(return_value={"status": "sent"})):
        result = await outreach_node(state)

    assert result["errors"] == []
