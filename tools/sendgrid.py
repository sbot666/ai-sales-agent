import httpx

SENDGRID_BASE = "https://api.sendgrid.com/v3"

async def send_email(
    api_key: str,
    from_email: str,
    to_email: str,
    subject: str,
    body: str,
    tracking_settings: dict | None = None,
) -> dict:
    payload = {
        "personalizations": [{"to": [{"email": to_email}], "subject": subject}],
        "from": {"email": from_email},
        "content": [{"type": "text/plain", "value": body}],
    }
    if tracking_settings:
        payload["tracking_settings"] = tracking_settings

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{SENDGRID_BASE}/mail/send",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"SendGrid API error {e.response.status_code}: {e.response.text}") from e
        except httpx.RequestError as e:
            raise RuntimeError(f"SendGrid request failed: {e}") from e
    return {"status": "sent", "to": to_email}
