"""HTTP client for PostHog API."""
from __future__ import annotations
import httpx
from typing import Any, Optional

DEFAULT_BASE = "https://us.posthog.com/api"

class PostHogClient:
    def __init__(self, api_key: str, base_url: str = ""):
        self.api_key = api_key.strip()
        self.base_url = (base_url.strip() if base_url else DEFAULT_BASE).rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Imperal-PostHog-Connector/1.0.0"
        }
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self._project_id: Optional[int] = None

    async def get_project_id(self, client: httpx.AsyncClient) -> int:
        if self._project_id:
            return self._project_id
        resp = await client.get(f"{self.base_url}/projects/@current/", headers=self.headers)
        if resp.status_code in (200, 201):
            data = resp.json()
            self._project_id = data.get("id")
            return self._project_id
        resp_list = await client.get(f"{self.base_url}/projects/", headers=self.headers)
        if resp_list.status_code in (200, 201):
            data = resp_list.json()
            results = data.get("results") or []
            if results and "id" in results[0]:
                self._project_id = results[0]["id"]
                return self._project_id
        raise ValueError(f"Unable to resolve PostHog project ID: HTTP {resp.status_code}")

    async def verify_auth(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(f"{self.base_url}/users/@me/", headers=self.headers)
                if resp.status_code in (200, 201):
                    return {"status": "ok", "data": resp.json() if resp.content else {}}
                return {"status": "error", "error": f"HTTP {resp.status_code}: {resp.text}"}
            except Exception as e:
                return {"status": "error", "error": str(e)}

    async def list_events(self, limit: int = 20) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            pid = await self.get_project_id(client)
            resp = await client.get(f"{self.base_url}/projects/{pid}/events/", headers=self.headers, params={"limit": limit})
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    return data
                for k in ["results", "data", "events", "items"]:
                    if k in data and isinstance(data[k], list):
                        return data[k]
                return []
            return []

    async def get_event(self, event_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            pid = await self.get_project_id(client)
            resp = await client.get(f"{self.base_url}/projects/{pid}/events/{event_id}/", headers=self.headers)
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"HTTP {resp.status_code}: {resp.text}"}

    async def audit_health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            auth_res = await self.verify_auth()
            events = await self.list_events(limit=10)
            return {
                "healthy": auth_res.get("status") == "ok",
                "total_events": len(events),
                "details": {
                    "auth": auth_res,
                    "sample_events": [str(e.get("id")) for e in events[:5]]
                }
            }

    async def create_action(self, name: str, event_name: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            pid = await self.get_project_id(client)
            payload = {
                "name": name,
                "steps": [{"event": event_name}]
            }
            resp = await client.post(f"{self.base_url}/projects/{pid}/actions/", headers=self.headers, json=payload)
            if resp.status_code in (200, 201):
                return resp.json()
            raise RuntimeError(f"Failed to create PostHog action: HTTP {resp.status_code} {resp.text}")

    async def list_actions(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            pid = await self.get_project_id(client)
            resp = await client.get(f"{self.base_url}/projects/{pid}/actions/", headers=self.headers)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("results") or []
            return []

    async def delete_action(self, action_id: str | int) -> bool:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            pid = await self.get_project_id(client)
            resp = await client.patch(f"{self.base_url}/projects/{pid}/actions/{action_id}/", headers=self.headers, json={"deleted": True})
            return resp.status_code in (200, 204)
