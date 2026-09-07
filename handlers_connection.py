"""Connection handlers for PostHog Connector."""
from __future__ import annotations
import uuid
from imperal_sdk import ActionResult
from app import chat
from schemas import NoParams, ConnectParams, ConnectionIdParams, ConnectionRecord, ConnectionList, DeleteResult
from posthog_connector_client import PostHogClient

async def get_connections_list(ctx) -> list[dict]:
    page = await ctx.store.query("connections")
    docs = page.data if hasattr(page, "data") else []
    conns = []
    for d in docs:
        data = d.data if hasattr(d, "data") else d
        doc_id = d.id if hasattr(d, "id") else data.get("id")
        data["_store_id"] = doc_id
        conns.append(data)
    return conns

async def resolve_client(ctx, connection_id: str = "") -> PostHogClient:
    conns = await get_connections_list(ctx)
    if not conns:
        raise ValueError("No PostHog connections configured. Use connect_posthog_connector first.")
    conn = None
    if connection_id:
        for c in conns:
            if c.get("id") == connection_id:
                conn = c
                break
        if not conn:
            raise ValueError(f"Connection {connection_id} not found.")
    else:
        conn = conns[0]
    return PostHogClient(api_key=conn["api_key"], base_url=conn.get("base_url", ""))

@chat.function("connect_posthog_connector", "Connect PostHog account via credentials.", action_type="write", chain_callable=True, event="posthog-connector.connect_posthog_connector", effects=["create:connection"], data_model=ConnectionRecord)
async def connect_posthog_connector(params: ConnectParams, ctx) -> ActionResult:
    client = PostHogClient(api_key=params.api_key, base_url=params.base_url)
    res = await client.verify_auth()
    if res.get("status") == "error":
        return ActionResult.error(f"Failed to authenticate with PostHog: {res.get('error')}")
    masked = params.api_key[:4] + "*" * (len(params.api_key) - 8) + params.api_key[-4:] if len(params.api_key) > 8 else "****"
    cid = f"conn_{uuid.uuid4().hex[:8]}"
    record = {
        "id": cid,
        "label": params.label.strip() or "PostHog Primary",
        "masked_key": masked,
        "api_key": params.api_key.strip(),
        "base_url": client.base_url,
        "is_active": True
    }
    await ctx.store.create("connections", record, id=cid)
    out = {k: v for k, v in record.items() if k != "api_key" and not k.startswith("_")}
    return ActionResult.success(out, summary=f"Connected PostHog account: {record['label']}.")

@chat.function("list_connections", "List configured PostHog connections.", action_type="read", chain_callable=True, event="posthog-connector.list_connections", effects=["read:connections"], data_model=ConnectionList)
async def list_connections(params: NoParams, ctx) -> ActionResult:
    conns = await get_connections_list(ctx)
    clean = [{k: v for k, v in c.items() if k != "api_key" and not k.startswith("_")} for c in conns]
    return ActionResult.success({"connections": clean, "total": len(clean)}, summary=f"Found {len(clean)} PostHog connections.")

@chat.function("disconnect_posthog_connector", "Disconnect PostHog account and delete stored credentials.", action_type="write", chain_callable=True, event="posthog-connector.disconnect_posthog_connector", effects=["delete:connection"], data_model=DeleteResult)
async def disconnect_posthog_connector(params: ConnectionIdParams, ctx) -> ActionResult:
    conns = await get_connections_list(ctx)
    target = None
    if params.connection_id:
        for c in conns:
            if c.get("id") == params.connection_id:
                target = c
                break
    elif conns:
        target = conns[0]
    if not target:
        return ActionResult.error(f"Connection {params.connection_id or 'default'} not found.")
    store_id = target.get("_store_id") or target.get("id")
    await ctx.store.delete("connections", store_id)
    return ActionResult.success({"success": True, "message": f"PostHog connection {target['id']} disconnected."}, summary=f"PostHog connection {target['id']} disconnected.")
