import pytest
import json
from unittest.mock import MagicMock, patch
from agents.state import make_initial_state
from agents.personalizer import personalizer_node

@pytest.mark.asyncio
async def test_personalizer_produces_email_drafts():
    leads = [
        {"email": "ceo@acme.io", "first_name": "Jane", "last_name": "Doe",
         "title": "CEO", "company": "Acme SaaS", "company_size": 100,
         "linkedin_url": None, "source": "apollo",
         "score": 85.0, "icp_match": 0.85, "reasoning": "Strong fit",
         "enrichment": {}},
    ]
    state = make_initial_state(run_config={"sequence_template": "demo-book"})
    state["scored_leads"] = leads

    mock_response_json = {
        "subject_a": "Quick question about Acme's pipeline",
        "subject_b": "Jane – 30% shorter sales cycles",
        "body": "Hi Jane,\n\nSaw Acme just raised Series A...\n\nWorth a 20-min call?\n\nBest,\nAlex",
    }
    with patch("agents.personalizer.anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=json.dumps(mock_response_json))]
        )
        result = await personalizer_node(state)

    assert len(result["email_drafts"]) == 1
    draft = result["email_drafts"][0]
    assert draft["email"] == "ceo@acme.io"
    assert draft["template_name"] == "demo-book"
    assert "subject_a" in draft
    assert "subject_b" in draft
    assert "body" in draft
    assert result["awaiting_approval"] is True

@pytest.mark.asyncio
async def test_personalizer_sets_awaiting_approval():
    state = make_initial_state(run_config={"sequence_template": "demo-book"})
    state["scored_leads"] = []
    with patch("agents.personalizer.anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        result = await personalizer_node(state)
    assert result["awaiting_approval"] is True
    assert result["email_drafts"] == []
