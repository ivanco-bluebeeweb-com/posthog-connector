"""Resource handlers for PostHog Connector."""
from __future__ import annotations
from typing import Any
from imperal_sdk import ActionResult
from app import chat
from schemas import (
    ListEventParams, GetEventParams,
    EventRecord, EventList, AuditHealthReport, ConnectionIdParams
)
from handlers_connection import resolve_client

@chat.function("list_events", "List events in PostHog.", action_type="read", chain_callable=True, event="posthog-connector.list_events", effects=["read:events"], data_model=EventList)
async def list_events(params: ListEventParams, ctx) -> ActionResult:
    client = await resolve_client(ctx, params.connection_id)
    try:
        raw_items = await client.list_events(limit=params.limit)
        items = []
        for r in raw_items:
            rid = str(r.get("id") or r.get("key") or r.get("uuid") or "unknown")
            rname = r.get("event") or r.get("name") or r.get("title") or rid
            items.append({
                "id": rid,
                "name": rname,
                "status": r.get("status") or "captured",
                "created_at": r.get("timestamp") or r.get("createdAt") or r.get("created_at"),
                "raw": r
            })
        return ActionResult.success({"events": items, "total": len(items)}, summary=f"Found {len(items)} events.")
    except Exception as e:
        return ActionResult.error(f"Error listing events: {e}")

@chat.function("get_event", "Get details of one Event in PostHog.", action_type="read", chain_callable=True, event="posthog-connector.get_event", effects=["read:event"], data_model=EventRecord)
async def get_event(params: GetEventParams, ctx) -> ActionResult:
    client = await resolve_client(ctx, params.connection_id)
    try:
        r = await client.get_event(params.event_id)
        if "error" in r and "id" not in r:
            return ActionResult.error(f"Error fetching event: {r.get('error')}")
        rid = str(r.get("id") or params.event_id)
        rname = r.get("event") or r.get("name") or r.get("title") or rid
        return ActionResult.success({
            "id": rid,
            "name": rname,
            "status": r.get("status") or "captured",
            "created_at": r.get("timestamp") or r.get("createdAt") or r.get("created_at"),
            "raw": r
        }, summary=f"Event {rid} details retrieved.")
    except Exception as e:
        return ActionResult.error(f"Error getting event: {e}")

@chat.function("audit_event_health", "Audit health of PostHog events and connectivity.", action_type="read", chain_callable=True, event="posthog-connector.audit_event_health", effects=["read:health"], data_model=AuditHealthReport)
async def audit_event_health(params: ConnectionIdParams, ctx) -> ActionResult:
    client = await resolve_client(ctx, params.connection_id)
    try:
        auth_res = await client.verify_auth()
        is_ok = auth_res.get("status") == "ok"
        events = await client.list_events(limit=10)
        healthy = is_ok and len(events) >= 0
        summary = f"PostHog connector health: {'healthy' if healthy else 'degraded'}. {len(events)} events inspected."
        return ActionResult.success({
            "healthy": healthy,
            "total_events": len(events),
            "details": {"auth": auth_res, "sample_count": len(events)},
            "summary": summary
        }, summary=summary)
    except Exception as e:
        return ActionResult.error(f"PostHog health audit failed: {e}")
