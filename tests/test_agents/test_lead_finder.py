import pytest
from unittest.mock import AsyncMock, patch
from agents.state import AgentState, make_initial_state
from agents.lead_finder import lead_finder_node

def base_config() -> dict:
    return {
        "apollo_api_key": "fake",
        "hunter_api_key": "fake",
        "titles": ["CEO"],
        "employee_range": [10, 500],
        "limit": 5,
        "linkedin_search_url": None,
        "csv_content": None,
        "linkedin_cookies": [],
    }

async def test_lead_finder_deduplicates_by_email():
    mock_leads = [
        {"email": "ceo@acme.io", "first_name": "Jane", "last_name": "Doe",
         "title": "CEO", "company": "Acme", "company_size": 100,
         "linkedin_url": None, "source": "apollo"},
        {"email": "ceo@acme.io", "first_name": "Jane", "last_name": "Doe",
         "title": "CEO", "company": "Acme", "company_size": 100,
         "linkedin_url": None, "source": "apollo"},
    ]
    state = make_initial_state(run_config=base_config())
    with patch("agents.lead_finder.apollo_search", AsyncMock(return_value=mock_leads)):
        with patch("agents.lead_finder.hunter_verify", AsyncMock(return_value={"status": "valid", "score": 90, "email": "ceo@acme.io"})):
            result = await lead_finder_node(state)

    emails = [l["email"] for l in result["raw_leads"]]
    assert emails.count("ceo@acme.io") == 1

async def test_lead_finder_includes_csv_leads():
    csv_content = "email,first_name,last_name,title,company\nfounder@startup.io,Bob,Smith,Founder,Startup\n"
    cfg = {**base_config(), "csv_content": csv_content, "apollo_api_key": "fake", "hunter_api_key": "fake"}
    state = make_initial_state(run_config=cfg)
    with patch("agents.lead_finder.apollo_search", AsyncMock(return_value=[])):
        result = await lead_finder_node(state)

    assert any(l["email"] == "founder@startup.io" for l in result["raw_leads"])

async def test_lead_finder_returns_error_on_apollo_failure():
    state = make_initial_state(run_config=base_config())
    with patch("agents.lead_finder.apollo_search", AsyncMock(side_effect=RuntimeError("API down"))):
        result = await lead_finder_node(state)

    assert len(result["errors"]) > 0
    assert "Apollo search failed" in result["errors"][0]
