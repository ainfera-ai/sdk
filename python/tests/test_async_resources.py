"""Happy-path tests for the async resource methods."""

from __future__ import annotations

import httpx
import pytest
import respx
from ainfera import AsyncAinferaClient


@pytest.mark.asyncio
async def test_async_agent_register(mock_api: respx.MockRouter) -> None:
    mock_api.post("/v1/agents").mock(
        return_value=httpx.Response(
            201, json={"agent_id": "ag_a", "name": "async", "description": None}
        )
    )
    client = AsyncAinferaClient(api_key="ak_test")
    try:
        agent = await client.agents.register(name="async")
        assert agent.agent_id == "ag_a"
        assert agent.name == "async"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_async_agent_refresh(mock_api: respx.MockRouter) -> None:
    mock_api.get("/v1/agents/ag_a").mock(
        side_effect=[
            httpx.Response(
                200, json={"agent_id": "ag_a", "name": "old", "description": None}
            ),
            httpx.Response(
                200, json={"agent_id": "ag_a", "name": "new", "description": "after"}
            ),
        ]
    )
    client = AsyncAinferaClient(api_key="ak_test")
    try:
        agent = await client.agents.retrieve("ag_a")
        assert agent.name == "old"
        returned = await agent.refresh()
        assert returned is agent
        assert agent.name == "new"
        assert agent.description == "after"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_async_inference(mock_api: respx.MockRouter) -> None:
    mock_api.get("/v1/agents/ag_a").mock(
        return_value=httpx.Response(
            200, json={"agent_id": "ag_a", "name": "x", "description": None}
        )
    )
    mock_api.post("/v1/agents/ag_a/inference").mock(
        return_value=httpx.Response(
            200,
            json={
                "text": "ok",
                "inference": {
                    "inference_id": "inf_a",
                    "agent_id": "ag_a",
                    "model": "claude-opus-4-7",
                    "messages": [],
                },
                "receipt": {
                    "receipt_id": "rcp_a",
                    "inference_id": "inf_a",
                    "audit_url": "https://ainfera.ai/audit/rcp_a",
                    "cost_usd": 0.0,
                },
            },
        )
    )
    client = AsyncAinferaClient(api_key="ak_test")
    try:
        agent = await client.agents.retrieve("ag_a")
        response = await agent.inference(model="claude-opus-4-7", messages=[])
        assert response.text == "ok"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_async_audit_chain_events(mock_api: respx.MockRouter) -> None:
    import hashlib
    from datetime import datetime, timezone

    from ainfera._internal.canonical import canonical_json

    def make(seq: int, payload: dict[str, object], prev: str | None) -> dict[str, object]:
        h = hashlib.sha256()
        h.update((prev or "").encode("utf-8"))
        h.update(canonical_json(payload))
        return {
            "event_id": f"ev_{seq}",
            "agent_id": "ag_a",
            "seq": seq,
            "event_type": "test",
            "payload": payload,
            "previous_hash": prev,
            "event_hash": h.hexdigest(),
            "created_at": datetime(2026, 5, 14, tzinfo=timezone.utc).isoformat(),
        }

    e0 = make(0, {"v": 0}, None)
    mock_api.get("/v1/agents/ag_a").mock(
        return_value=httpx.Response(
            200, json={"agent_id": "ag_a", "name": "x", "description": None}
        )
    )
    mock_api.get("/v1/agents/ag_a/audit").mock(
        return_value=httpx.Response(200, json={"data": [e0]})
    )
    client = AsyncAinferaClient(api_key="ak_test")
    try:
        agent = await client.agents.retrieve("ag_a")
        events = [event async for event in agent.audit_chain.events(limit=10)]
        assert len(events) == 1
        assert events[0].seq == 0
        assert await agent.audit_chain.verify() is True
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_async_audit_chain_paginates_across_cursors(
    mock_api: respx.MockRouter,
) -> None:
    import hashlib
    from datetime import datetime, timezone

    from ainfera._internal.canonical import canonical_json

    def make(seq: int, payload: dict[str, object], prev: str | None) -> dict[str, object]:
        h = hashlib.sha256()
        h.update((prev or "").encode("utf-8"))
        h.update(canonical_json(payload))
        return {
            "event_id": f"ev_{seq}",
            "agent_id": "ag_a",
            "seq": seq,
            "event_type": "test",
            "payload": payload,
            "previous_hash": prev,
            "event_hash": h.hexdigest(),
            "created_at": datetime(2026, 5, 14, tzinfo=timezone.utc).isoformat(),
        }

    e0 = make(0, {"v": 0}, None)
    e1 = make(1, {"v": 1}, str(e0["event_hash"]))

    mock_api.get("/v1/agents/ag_a").mock(
        return_value=httpx.Response(
            200, json={"agent_id": "ag_a", "name": "x", "description": None}
        )
    )
    mock_api.get("/v1/agents/ag_a/audit", params={"cursor": "cursor_2"}).mock(
        return_value=httpx.Response(200, json={"data": [e1], "next_cursor": None})
    )
    mock_api.get("/v1/agents/ag_a/audit").mock(
        return_value=httpx.Response(200, json={"data": [e0], "next_cursor": "cursor_2"})
    )

    client = AsyncAinferaClient(api_key="ak_test")
    try:
        agent = await client.agents.retrieve("ag_a")
        events = [event async for event in agent.audit_chain.events()]
        assert [e.seq for e in events] == [0, 1]
        assert await agent.audit_chain.verify() is True
    finally:
        await client.aclose()
