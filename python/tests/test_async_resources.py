"""Happy-path tests for the async resource methods.

SDK 1.1.0 (AIN-79) fixtures: mirrors test_resources.py against the
production `/v1/*` surface.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import httpx
import pytest
import respx
from ainfera import AsyncAinferaClient
from ainfera._internal.canonical import canonical_json

_AID = "ag_a"


def _agent_body() -> dict[str, object]:
    return {
        "id": _AID,
        "tenant_id": "tn_1",
        "name": "x",
        "status": "active",
        "public_key_ed25519": "-----BEGIN PUBLIC KEY-----\nFAKEPEM\n-----END PUBLIC KEY-----\n",
        "created_at": "2026-05-14T00:00:00Z",
    }


@pytest.mark.asyncio
async def test_async_agent_register(mock_api: respx.MockRouter) -> None:
    mock_api.post("/v1/agents/register").mock(
        return_value=httpx.Response(
            201, json={**_agent_body(), "name": "async"}
        )
    )
    client = AsyncAinferaClient(api_key="ak_test")
    try:
        agent = await client.agents.register(tenant_id="tn_1", name="async")
        assert agent.agent_id == _AID
        assert agent.name == "async"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_async_agent_refresh(mock_api: respx.MockRouter) -> None:
    mock_api.get(f"/v1/agents/{_AID}").mock(
        side_effect=[
            httpx.Response(200, json={**_agent_body(), "name": "old"}),
            httpx.Response(200, json={**_agent_body(), "name": "new"}),
        ]
    )
    client = AsyncAinferaClient(api_key="ak_test")
    try:
        agent = await client.agents.retrieve(_AID)
        assert agent.name == "old"
        returned = await agent.refresh()
        assert returned is agent
        assert agent.name == "new"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_async_inference(mock_api: respx.MockRouter) -> None:
    mock_api.get(f"/v1/agents/{_AID}").mock(
        return_value=httpx.Response(200, json=_agent_body())
    )
    route = mock_api.post("/v1/inference").mock(
        return_value=httpx.Response(
            200,
            json={
                "inference_id": "inf_a",
                "receipt_id": "rcp_a",
                "content": "ok",
                "model_used": "claude-opus-4-7",
                "provider": "anthropic",
                "finish_reason": "stop",
                "input_tokens": 1,
                "output_tokens": 1,
                "cost_usd": "0.0",
            },
        )
    )
    client = AsyncAinferaClient(api_key="ak_test")
    try:
        agent = await client.agents.retrieve(_AID)
        response = await agent.inference(model="claude-opus-4-7", messages=[])
        assert response.content == "ok"
        # Body carries agent_id
        sent_body = json.loads(route.calls.last.request.content)
        assert sent_body["agent_id"] == _AID
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_async_audit_chain_events(mock_api: respx.MockRouter) -> None:
    def make(seq: int, payload: dict[str, object], prev: str | None) -> dict[str, object]:
        h = hashlib.sha256()
        h.update((prev or "").encode("utf-8"))
        h.update(canonical_json(payload))
        return {
            "id": f"ev_{seq}",
            "agent_id": _AID,
            "seq": seq,
            "event_type": "test",
            "payload": payload,
            "previous_hash": prev,
            "event_hash": h.hexdigest(),
            "created_at": datetime(2026, 5, 14, tzinfo=timezone.utc).isoformat(),
        }

    e0 = make(0, {"v": 0}, None)
    mock_api.get(f"/v1/agents/{_AID}").mock(
        return_value=httpx.Response(200, json=_agent_body())
    )

    def handler(request: httpx.Request) -> httpx.Response:
        since_raw = request.url.params.get("since_seq")
        since = int(since_raw) if since_raw is not None else -1
        page = [e for e in [e0] if int(e["seq"]) > since]
        return httpx.Response(200, json={"agent_id": _AID, "events": page})

    mock_api.get(f"/v1/audit/{_AID}").mock(side_effect=handler)
    client = AsyncAinferaClient(api_key="ak_test")
    try:
        agent = await client.agents.retrieve(_AID)
        events = [event async for event in agent.audit_chain.events(limit=10)]
        assert len(events) == 1
        assert events[0].seq == 0
        assert await agent.audit_chain.verify() is True
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_async_audit_chain_paginates_via_since_seq(
    mock_api: respx.MockRouter,
) -> None:
    def make(seq: int, payload: dict[str, object], prev: str | None) -> dict[str, object]:
        h = hashlib.sha256()
        h.update((prev or "").encode("utf-8"))
        h.update(canonical_json(payload))
        return {
            "id": f"ev_{seq}",
            "agent_id": _AID,
            "seq": seq,
            "event_type": "test",
            "payload": payload,
            "previous_hash": prev,
            "event_hash": h.hexdigest(),
            "created_at": datetime(2026, 5, 14, tzinfo=timezone.utc).isoformat(),
        }

    e0 = make(0, {"v": 0}, None)
    e1 = make(1, {"v": 1}, str(e0["event_hash"]))

    mock_api.get(f"/v1/agents/{_AID}").mock(
        return_value=httpx.Response(200, json=_agent_body())
    )

    def handler(request: httpx.Request) -> httpx.Response:
        since = request.url.params.get("since_seq")
        if since is None:
            return httpx.Response(200, json={"agent_id": _AID, "events": [e0]})
        if since == "0":
            return httpx.Response(200, json={"agent_id": _AID, "events": [e1]})
        return httpx.Response(200, json={"agent_id": _AID, "events": []})

    mock_api.get(f"/v1/audit/{_AID}").mock(side_effect=handler)

    client = AsyncAinferaClient(api_key="ak_test")
    try:
        agent = await client.agents.retrieve(_AID)
        events = [event async for event in agent.audit_chain.events(limit=2)]
        assert [e.seq for e in events] == [0, 1]
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_async_agent_wallet_awaitable(mock_api: respx.MockRouter) -> None:
    """AIN-196: AsyncAgent.wallet is awaitable, not a mistaken sync property."""
    mock_api.get(f"/v1/agents/{_AID}").mock(
        return_value=httpx.Response(200, json=_agent_body())
    )
    wallet_route = mock_api.get(f"/v1/wallets/{_AID}").mock(
        return_value=httpx.Response(
            200, json={"agent_id": _AID, "balance_usd": "3.50"}
        )
    )
    client = AsyncAinferaClient(api_key="ak_test")
    try:
        agent = await client.agents.retrieve(_AID)
        wallet = await agent.wallet
        assert float(wallet.balance_usd) == 3.5
        assert wallet_route.call_count == 1
        again = await agent.get_wallet()
        assert float(again.balance_usd) == 3.5
        assert wallet_route.call_count == 1
    finally:
        await client.aclose()
