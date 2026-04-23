import pytest
from unittest.mock import AsyncMock, patch
from tools.hunter import hunter_verify

@pytest.mark.asyncio
async def test_hunter_verify_valid_email():
    mock_response = {"data": {"status": "valid", "score": 92}}
    with patch("tools.hunter.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_resp = AsyncMock()
        mock_resp.json = lambda: mock_response  # json() is sync in httpx
        mock_resp.raise_for_status = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        result = await hunter_verify("fake_key", "ceo@acme.io")

    assert result["status"] == "valid"
    assert result["score"] == 92
    assert result["email"] == "ceo@acme.io"
