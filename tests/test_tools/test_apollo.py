import pytest
from unittest.mock import AsyncMock, patch
import httpx
from tools.apollo import apollo_search

@pytest.mark.asyncio
async def test_apollo_search_returns_leads():
    mock_response = {
        "people": [
            {
                "email": "ceo@acme.io",
                "first_name": "Jane",
                "last_name": "Doe",
                "title": "CEO",
                "linkedin_url": "https://linkedin.com/in/janedoe",
                "organization": {"name": "Acme", "estimated_num_employees": 150},
            }
        ]
    }
    with patch("tools.apollo.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_resp = AsyncMock()
        mock_resp.json = lambda: mock_response  # json() is sync in httpx
        mock_resp.raise_for_status = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        leads = await apollo_search("fake_key", ["CEO", "CTO"], (10, 500), limit=10)

    assert len(leads) == 1
    assert leads[0]["email"] == "ceo@acme.io"
    assert leads[0]["company"] == "Acme"

@pytest.mark.asyncio
async def test_apollo_search_filters_missing_email():
    mock_response = {
        "people": [
            {"first_name": "No", "last_name": "Email", "title": "CEO", "organization": {"name": "X"}},
        ]
    }
    with patch("tools.apollo.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_resp = AsyncMock()
        mock_resp.json = lambda: mock_response  # json() is sync in httpx
        mock_resp.raise_for_status = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        leads = await apollo_search("fake_key", ["CEO"], (10, 500))

    assert leads == []

@pytest.mark.asyncio
async def test_apollo_search_raises_on_api_error():
    with patch("tools.apollo.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_resp = AsyncMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        mock_client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError("401", request=AsyncMock(), response=mock_resp)
        )
        mock_client_cls.return_value = mock_client

        with pytest.raises(RuntimeError, match="Apollo API error"):
            await apollo_search("bad_key", ["CEO"], (10, 500))
