import pytest
import json
from unittest.mock import MagicMock, patch
from agents.state import make_initial_state
from agents.scorer import scorer_node

async def test_scorer_filters_below_threshold():
    leads = [
        {"email": "ceo@acme.io", "first_name": "Jane", "last_name": "Doe",
         "title": "CEO", "company": "Acme SaaS", "company_size": 100,
         "linkedin_url": None, "source": "apollo"},
        {"email": "intern@corp.com", "first_name": "Bob", "last_name": "Smith",
         "title": "Intern", "company": "MegaCorp", "company_size": 10000,
         "linkedin_url": None, "source": "apollo"},
    ]
    state = make_initial_state(run_config={})
    state["raw_leads"] = leads

    responses = [
        MagicMock(content=[MagicMock(text=json.dumps({"score": 85, "icp_match": 0.85, "reasoning": "CEO at SaaS"}))]),
        MagicMock(content=[MagicMock(text=json.dumps({"score": 20, "icp_match": 0.20, "reasoning": "Intern at enterprise"}))]),
    ]

    with patch("agents.scorer.anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.side_effect = responses
        result = await scorer_node(state)

    assert len(result["scored_leads"]) == 1
    assert result["scored_leads"][0]["email"] == "ceo@acme.io"
    assert result["scored_leads"][0]["score"] == 85

async def test_scorer_skips_leads_on_api_error():
    leads = [
        {"email": "ceo@acme.io", "first_name": "Jane", "last_name": "Doe",
         "title": "CEO", "company": "Acme", "company_size": 100,
         "linkedin_url": None, "source": "apollo"},
    ]
    state = make_initial_state(run_config={})
    state["raw_leads"] = leads

    with patch("agents.scorer.anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API error")
        result = await scorer_node(state)

    assert result["scored_leads"] == []
