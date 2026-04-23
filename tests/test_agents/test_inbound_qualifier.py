import pytest
import json
from unittest.mock import MagicMock, patch
from agents.inbound_qualifier import inbound_qualifier_node

def make_inbound_state(messages: list, lead_email: str) -> dict:
    return {
        "run_config": {"calendly_event_url": "https://calendly.com/test/30min"},
        "inbound_conversation": {"email": lead_email, "messages": messages},
    }

async def test_inbound_qualifier_asks_next_question_when_incomplete():
    state = make_inbound_state(
        messages=[{"role": "user", "content": "Hi, I'm interested in your product"}],
        lead_email="founder@startup.io",
    )
    mock_response = json.dumps({"qualified": None, "next_message": "What problem are you trying to solve?"})
    with patch("agents.inbound_qualifier.anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=mock_response)]
        )
        result = await inbound_qualifier_node(state)
    assert result["inbound_result"]["qualified"] is None
    assert "next_message" in result["inbound_result"]

async def test_inbound_qualifier_routes_qualified_lead():
    messages = [
        {"role": "user", "content": "Hi, interested in your product"},
        {"role": "assistant", "content": "What problem are you solving?"},
        {"role": "user", "content": "We need to automate sales outreach. Budget 20K/yr, I'm the CEO, need it within a month."},
    ]
    state = make_inbound_state(messages=messages, lead_email="ceo@startup.io")
    mock_response = json.dumps({
        "qualified": True, "score": 90,
        "bant": {"budget": "20K/yr", "authority": "CEO", "need": "automate outreach", "timeline": "1 month"},
        "next_message": "Great! Book a call: https://calendly.com/test/30min?email=ceo@startup.io",
    })
    with patch("agents.inbound_qualifier.anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=mock_response)]
        )
        result = await inbound_qualifier_node(state)
    assert result["inbound_result"]["qualified"] is True
    assert result["inbound_result"]["score"] == 90
