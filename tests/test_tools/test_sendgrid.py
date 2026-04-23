import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from tools.sendgrid import send_email

async def test_send_email_calls_api():
    with patch("tools.sendgrid.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_resp = MagicMock()
        mock_resp.status_code = 202
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_cls.return_value = mock_client
        result = await send_email("SG.fake", "out@co.io", "ceo@acme.io", "Hello", "Hi Jane")
    assert result["status"] == "sent"

async def test_send_email_raises_on_api_error():
    with patch("tools.sendgrid.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.text = "Forbidden"
        mock_client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError("403", request=MagicMock(), response=mock_resp)
        )
        mock_cls.return_value = mock_client
        with pytest.raises(RuntimeError, match="SendGrid API error"):
            await send_email("bad_key", "out@co.io", "ceo@acme.io", "Hello", "Hi Jane")
