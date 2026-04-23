import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from agents.state import make_initial_state
from agents.follow_up import follow_up_node

def make_follow_up_state(reply_content: str, lead_email: str) -> dict:
    state = make_initial_state(run_config={
        "calendly_api_key": "fake",
        "calendly_event_url": "https://calendly.com/test/30min",
        "sendgrid_api_key": "SG.fake",
        "from_email": "out@co.io",
    })
    state["reply_event"] = {"email": lead_email, "content": reply_content}
    return state

async def test_follow_up_routes_interested_to_calendly():
    state = make_follow_up_state("Yes, I'd love to chat!", "ceo@acme.io")
    mock_classify = {"sentiment": "interested", "objection_type": None, "summary": "Positive reply"}
    with patch("agents.follow_up.anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=json.dumps(mock_classify))]
        )
        with patch("agents.follow_up.send_email", AsyncMock(return_value={"status": "sent"})):
            result = await follow_up_node(state)
    assert result["follow_up_action"] == "calendly_sent"

async def test_follow_up_handles_objection():
    state = make_follow_up_state("Too expensive for us right now.", "ceo@acme.io")
    mock_classify = {"sentiment": "objection", "objection_type": "price", "summary": "Price concern"}
    with patch("agents.follow_up.anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.side_effect = [
            MagicMock(content=[MagicMock(text=json.dumps(mock_classify))]),
            MagicMock(content=[MagicMock(text="I understand budget is tight...")]),
        ]
        with patch("agents.follow_up.send_email", AsyncMock(return_value={"status": "sent"})):
            result = await follow_up_node(state)
    assert result["follow_up_action"] == "objection_handled"

async def test_follow_up_marks_not_interested():
    state = make_follow_up_state("Please remove me from your list.", "ceo@acme.io")
    mock_classify = {"sentiment": "not_interested", "objection_type": None, "summary": "Unsubscribe request"}
    with patch("agents.follow_up.anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=json.dumps(mock_classify))]
        )
        result = await follow_up_node(state)
    assert result["follow_up_action"] == "unsubscribed"
