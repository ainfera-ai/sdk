"""Happy-path tests for the sync resource methods (Agent, Wallet, AuditChain, Receipts)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import httpx
import pytest
import respx
from ainfera import AinferaClient
from ainfera._internal.canonical import canonical_json


def test_agent_register(mock_api: respx.MockRouter) -> None:
    mock_api.post("/v1/agents").mock(
        return_value=httpx.Response(
            201,
            json={"agent_id": "ag_42", "name": "my-agent", "description": "test"},
        )
    )
    client = AinferaClient(api_key="ak_test")
    agent = client.agents.register(name="my-agent", description="test")
    assert agent.agent_id == "ag_42"
    assert agent.name == "my-agent"


def test_agent_retrieve(mock_api: respx.MockRouter) -> None:
    mock_api.get("/v1/agents/ag_42").mock(
        return_value=httpx.Response(
            200, json={"agent_id": "ag_42", "name": "x", "description": None}
        )
    )
    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve("ag_42")
    assert agent.agent_id == "ag_42"


def test_agent_refresh_updates_fields(mock_api: respx.MockRouter) -> None:
    mock_api.get("/v1/agents/ag_x").mock(
        side_effect=[
            httpx.Response(
                200, json={"agent_id": "ag_x", "name": "old", "description": "before"}
            ),
            httpx.Response(
                200, json={"agent_id": "ag_x", "name": "new", "description": "after"}
            ),
        ]
    )
    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve("ag_x")
    assert agent.name == "old"
    returned = agent.refresh()
    assert returned is agent
    assert agent.name == "new"
    assert agent.description == "after"


def test_agent_refresh_clears_wallet_cache(mock_api: respx.MockRouter) -> None:
    mock_api.get("/v1/agents/ag_x").mock(
        return_value=httpx.Response(
            200, json={"agent_id": "ag_x", "name": "n", "description": None}
        )
    )
    wallet_route = mock_api.get("/v1/agents/ag_x/wallet").mock(
        return_value=httpx.Response(
            200, json={"wallet_id": "w_1", "agent_id": "ag_x", "balance_usd": 0.0}
        )
    )
    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve("ag_x")
    _ = agent.wallet.balance_usd
    assert wallet_route.call_count == 1
    _ = agent.wallet.balance_usd  # cached — no second fetch
    assert wallet_route.call_count == 1
    agent.refresh()
    _ = agent.wallet.balance_usd  # cache dropped — re-fetched
    assert wallet_route.call_count == 2


def test_wallet_topup(mock_api: respx.MockRouter) -> None:
    mock_api.get("/v1/agents/ag_x/wallet").mock(
        return_value=httpx.Response(
            200, json={"wallet_id": "w_1", "agent_id": "ag_x", "balance_usd": 0.0}
        )
    )
    mock_api.post("/v1/agents/ag_x/wallet/topup").mock(
        return_value=httpx.Response(
            200, json={"wallet_id": "w_1", "agent_id": "ag_x", "balance_usd": 10.0}
        )
    )
    mock_api.get("/v1/agents/ag_x").mock(
        return_value=httpx.Response(
            200, json={"agent_id": "ag_x", "name": "n", "description": None}
        )
    )
    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve("ag_x")
    agent.wallet.topup(amount_usd=10)
    assert agent.wallet.balance_usd == 10.0


def test_inference_returns_response(mock_api: respx.MockRouter) -> None:
    mock_api.get("/v1/agents/ag_x").mock(
        return_value=httpx.Response(
            200, json={"agent_id": "ag_x", "name": "n", "description": None}
        )
    )
    mock_api.post("/v1/agents/ag_x/inference").mock(
        return_value=httpx.Response(
            200,
            json={
                "text": "Hello!",
                "inference": {
                    "inference_id": "inf_1",
                    "agent_id": "ag_x",
                    "model": "claude-opus-4-7",
                    "messages": [{"role": "user", "content": "Hi"}],
                },
                "receipt": {
                    "receipt_id": "rcp_1",
                    "inference_id": "inf_1",
                    "audit_url": "https://ainfera.ai/audit/rcp_1",
                    "cost_usd": 0.0042,
                },
            },
        )
    )
    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve("ag_x")
    response = agent.inference(
        model="claude-opus-4-7",
        messages=[{"role": "user", "content": "Hi"}],
    )
    assert response.text == "Hello!"
    assert response.receipt.audit_url == "https://ainfera.ai/audit/rcp_1"
    assert response.receipt.cost_usd == pytest.approx(0.0042)


def test_audit_chain_events_and_verify(mock_api: respx.MockRouter) -> None:
    def make_event(seq: int, payload: dict[str, object], prev: str | None) -> dict[str, object]:
        h = hashlib.sha256()
        h.update((prev or "").encode("utf-8"))
        h.update(canonical_json(payload))
        return {
            "event_id": f"ev_{seq}",
            "agent_id": "ag_x",
            "seq": seq,
            "event_type": "test",
            "payload": payload,
            "previous_hash": prev,
            "event_hash": h.hexdigest(),
            "created_at": datetime(2026, 5, 14, tzinfo=timezone.utc).isoformat(),
        }

    e0 = make_event(0, {"v": 0}, None)
    e1 = make_event(1, {"v": 1}, str(e0["event_hash"]))
    e2 = make_event(2, {"v": 2}, str(e1["event_hash"]))

    mock_api.get("/v1/agents/ag_x").mock(
        return_value=httpx.Response(
            200, json={"agent_id": "ag_x", "name": "n", "description": None}
        )
    )
    mock_api.get("/v1/agents/ag_x/audit").mock(
        return_value=httpx.Response(200, json={"data": [e0, e1, e2]})
    )

    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve("ag_x")
    events = list(agent.audit_chain.events(limit=10))
    assert len(events) == 3
    assert events[2].seq == 2
    assert agent.audit_chain.verify() is True


def test_audit_chain_paginates_across_cursors(mock_api: respx.MockRouter) -> None:
    def make_event(seq: int, payload: dict[str, object], prev: str | None) -> dict[str, object]:
        h = hashlib.sha256()
        h.update((prev or "").encode("utf-8"))
        h.update(canonical_json(payload))
        return {
            "event_id": f"ev_{seq}",
            "agent_id": "ag_x",
            "seq": seq,
            "event_type": "test",
            "payload": payload,
            "previous_hash": prev,
            "event_hash": h.hexdigest(),
            "created_at": datetime(2026, 5, 14, tzinfo=timezone.utc).isoformat(),
        }

    e0 = make_event(0, {"v": 0}, None)
    e1 = make_event(1, {"v": 1}, str(e0["event_hash"]))
    e2 = make_event(2, {"v": 2}, str(e1["event_hash"]))

    mock_api.get("/v1/agents/ag_x").mock(
        return_value=httpx.Response(
            200, json={"agent_id": "ag_x", "name": "n", "description": None}
        )
    )
    # Page 2 — matched first because it carries the cursor query param.
    mock_api.get("/v1/agents/ag_x/audit", params={"cursor": "cursor_2"}).mock(
        return_value=httpx.Response(200, json={"data": [e2], "next_cursor": None})
    )
    # Page 1 — the cursorless first request falls through to here.
    mock_api.get("/v1/agents/ag_x/audit").mock(
        return_value=httpx.Response(200, json={"data": [e0, e1], "next_cursor": "cursor_2"})
    )

    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve("ag_x")
    events = list(agent.audit_chain.events())
    assert [e.seq for e in events] == [0, 1, 2]
    assert agent.audit_chain.verify() is True


def test_audit_chain_limit_stops_before_next_page(mock_api: respx.MockRouter) -> None:
    def make_event(seq: int) -> dict[str, object]:
        return {
            "event_id": f"ev_{seq}",
            "agent_id": "ag_x",
            "seq": seq,
            "event_type": "test",
            "payload": {"v": seq},
            "previous_hash": None,
            "event_hash": "0" * 64,
            "created_at": datetime(2026, 5, 14, tzinfo=timezone.utc).isoformat(),
        }

    mock_api.get("/v1/agents/ag_x").mock(
        return_value=httpx.Response(
            200, json={"agent_id": "ag_x", "name": "n", "description": None}
        )
    )
    page_one = mock_api.get("/v1/agents/ag_x/audit").mock(
        return_value=httpx.Response(
            200,
            json={"data": [make_event(0), make_event(1)], "next_cursor": "cursor_2"},
        )
    )

    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve("ag_x")
    events = list(agent.audit_chain.events(limit=2))
    assert len(events) == 2
    # limit satisfied within page one — the cursor must not be followed.
    assert page_one.call_count == 1


def test_inference_accepts_per_call_timeout(mock_api: respx.MockRouter) -> None:
    mock_api.get("/v1/agents/ag_x").mock(
        return_value=httpx.Response(
            200, json={"agent_id": "ag_x", "name": "n", "description": None}
        )
    )
    route = mock_api.post("/v1/agents/ag_x/inference").mock(
        return_value=httpx.Response(
            200,
            json={
                "text": "ok",
                "inference": {
                    "inference_id": "inf_1",
                    "agent_id": "ag_x",
                    "model": "claude-opus-4-7",
                    "messages": [],
                },
                "receipt": {
                    "receipt_id": "rcp_1",
                    "inference_id": "inf_1",
                    "audit_url": "https://ainfera.ai/audit/rcp_1",
                    "cost_usd": 0.0,
                },
            },
        )
    )
    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve("ag_x")
    response = agent.inference(model="claude-opus-4-7", messages=[], timeout=120.0)
    assert response.text == "ok"
    assert route.calls.last.request.extensions["timeout"]["read"] == 120.0


def test_receipt_retrieve(mock_api: respx.MockRouter) -> None:
    mock_api.get("/v1/receipts/rcp_1").mock(
        return_value=httpx.Response(
            200,
            json={
                "receipt_id": "rcp_1",
                "inference_id": "inf_1",
                "audit_url": "https://ainfera.ai/audit/rcp_1",
                "cost_usd": 0.01,
            },
        )
    )
    client = AinferaClient(api_key="ak_test")
    receipt = client.receipts.retrieve("rcp_1")
    assert receipt.receipt_id == "rcp_1"
    assert receipt.cost_usd == pytest.approx(0.01)


def test_register_body_carries_payload(mock_api: respx.MockRouter) -> None:
    route = mock_api.post("/v1/agents").mock(
        return_value=httpx.Response(
            201, json={"agent_id": "ag_1", "name": "test", "description": "d"}
        )
    )
    client = AinferaClient(api_key="ak_test")
    client.agents.register(name="test", description="d")
    sent = route.calls.last.request
    assert json.loads(sent.content) == {"name": "test", "description": "d"}
