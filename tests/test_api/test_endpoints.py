import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from api.main import app

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

async def test_outbound_run_endpoint(client):
    mock_result = {"email_drafts": [], "raw_leads": [], "scored_leads": [], "errors": [], "approved_drafts": [], "awaiting_approval": True}
    with patch("api.main.build_outbound_pipeline") as mock_build:
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value=mock_result)
        mock_build.return_value = mock_graph
        resp = await client.post("/api/run/outbound", json={"titles": ["CEO"], "employee_range": [10, 500], "limit": 5, "sequence_template": "demo-book"})
    assert resp.status_code == 200
    assert "run_id" in resp.json()

async def test_inbound_run_endpoint(client):
    with patch("api.main.build_inbound_pipeline") as mock_build:
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value={"inbound_result": {"qualified": None, "next_message": "What problem are you solving?"}})
        mock_build.return_value = mock_graph
        resp = await client.post("/api/run/inbound", json={"email": "founder@startup.io", "messages": [{"role": "user", "content": "Hi, I'm interested"}]})
    assert resp.status_code == 200
    assert "next_message" in resp.json()

async def test_approve_endpoint(client):
    resp = await client.post("/api/approve", json={"run_id": "test-run-123", "approved_emails": ["ceo@acme.io"]})
    assert resp.status_code == 200

async def test_reply_webhook_endpoint(client):
    with patch("api.main.build_follow_up_pipeline") as mock_build:
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value={"follow_up_action": "calendly_sent", "errors": []})
        mock_build.return_value = mock_graph
        resp = await client.post("/api/reply", json={"email": "ceo@acme.io", "content": "Yes, let's chat!", "timestamp": "2026-04-23T10:00:00Z"})
    assert resp.status_code == 200
