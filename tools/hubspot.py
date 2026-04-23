import httpx

HUBSPOT_BASE = "https://api.hubapi.com"

async def upsert_contact(access_token: str, email: str, properties: dict) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{HUBSPOT_BASE}/crm/v3/objects/contacts",
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                json={"properties": {"email": email, **properties}},
            )
            if resp.status_code == 409:
                contact_id = resp.json().get("message", "").split("ID: ")[-1]
                patch = await client.patch(
                    f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{contact_id}",
                    headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                    json={"properties": properties},
                )
                patch.raise_for_status()
                return patch.json()
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"HubSpot API error {e.response.status_code}") from e
