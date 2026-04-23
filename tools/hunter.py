import httpx

HUNTER_BASE = "https://api.hunter.io/v2"

async def hunter_verify(api_key: str, email: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{HUNTER_BASE}/email-verifier",
                params={"email": email, "api_key": api_key},
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Hunter API error {e.response.status_code}: {e.response.text}") from e
        except httpx.RequestError as e:
            raise RuntimeError(f"Hunter request failed: {e}") from e

        body = resp.json()
        data = body.get("data", {})
        return {
            "email": email,
            "status": data.get("status", "unknown"),
            "score": data.get("score", 0),
        }
