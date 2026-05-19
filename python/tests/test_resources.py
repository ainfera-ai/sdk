"""Happy-path tests for the sync resource methods (Agent, Wallet, AuditChain, Receipts).

SDK 1.1.0 (AIN-79) fixtures: paths + response shapes mirror the production
``/v1/*`` surface verified against ``ainfera_api/routers/`` on 2026-05-19.
The 1.0.x fixtures used pre-D4 mock shapes that didn't round-trip.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import httpx
import pytest
import respx
from ainfera import AinferaClient
from ainfera._internal.canonical import canonical_json

# Fixture constants — the test agent id used across mocked routes.
_AID = "ag_42"


def _agent_body(*, agent_id: str = _AID, name: str = "n") -> dict[str, object]:
    """The canonical retrieve-response shape used across happy-path tests."""
    return {
        "id": agent_id,
        "tenant_id": "tn_1",
        "name": name,
        "status": "active",
        "public_key_ed25519": "-----BEGIN PUBLIC KEY-----\nFAKEPEM\n-----END PUBLIC KEY-----\n",
        "created_at": "2026-05-14T00:00:00Z",
    }


def test_agent_register(mock_api: respx.MockRouter) -> None:
    mock_api.post("/v1/agents/register").mock(
        return_value=httpx.Response(201, json=_agent_body(name="my-agent"))
    )
    client = AinferaClient(api_key="ak_test")
    agent = client.agents.register(tenant_id="tn_1", name="my-agent")
    assert agent.agent_id == _AID
    assert agent.name == "my-agent"
    assert agent.tenant_id == "tn_1"


def test_agent_retrieve(mock_api: respx.MockRouter) -> None:
    mock_api.get(f"/v1/agents/{_AID}").mock(
        return_value=httpx.Response(200, json=_agent_body())
    )
    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve(_AID)
    assert agent.agent_id == _AID
    assert agent.status == "active"


def test_agent_register_body_carries_payload(mock_api: respx.MockRouter) -> None:
    route = mock_api.post("/v1/agents/register").mock(
        return_value=httpx.Response(201, json=_agent_body(name="test"))
    )
    client = AinferaClient(api_key="ak_test")
    client.agents.register(tenant_id="tn_1", name="test")
    sent = route.calls.last.request
    assert json.loads(sent.content) == {"tenant_id": "tn_1", "name": "test"}


def test_agent_refresh_updates_fields(mock_api: respx.MockRouter) -> None:
    mock_api.get(f"/v1/agents/{_AID}").mock(
        side_effect=[
            httpx.Response(200, json=_agent_body(name="old")),
            httpx.Response(200, json=_agent_body(name="new")),
        ]
    )
    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve(_AID)
    assert agent.name == "old"
    returned = agent.refresh()
    assert returned is agent
    assert agent.name == "new"


def test_agent_refresh_clears_wallet_cache(mock_api: respx.MockRouter) -> None:
    mock_api.get(f"/v1/agents/{_AID}").mock(
        return_value=httpx.Response(200, json=_agent_body())
    )
    wallet_route = mock_api.get(f"/v1/wallets/{_AID}").mock(
        return_value=httpx.Response(200, json={"agent_id": _AID, "balance_usd": "0"})
    )
    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve(_AID)
    _ = agent.wallet.balance_usd
    assert wallet_route.call_count == 1
    _ = agent.wallet.balance_usd
    assert wallet_route.call_count == 1
    agent.refresh()
    _ = agent.wallet.balance_usd
    assert wallet_route.call_count == 2


def test_wallet_topup(mock_api: respx.MockRouter) -> None:
    mock_api.get(f"/v1/wallets/{_AID}").mock(
        return_value=httpx.Response(200, json={"agent_id": _AID, "balance_usd": "0"})
    )
    mock_api.post("/v1/wallets/topup").mock(
        return_value=httpx.Response(
            201,
            json={
                "agent_id": _AID,
                "amount_usd": "10",
                "new_balance_usd": "10",
                "ledger_entry_id": "le_1",
                "audit_event_id": "ae_1",
            },
        )
    )
    mock_api.get(f"/v1/agents/{_AID}").mock(
        return_value=httpx.Response(200, json=_agent_body())
    )
    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve(_AID)
    agent.wallet.topup(amount_usd=10)
    assert float(agent.wallet.balance_usd) == 10.0


def test_wallet_topup_body_carries_agent_id(mock_api: respx.MockRouter) -> None:
    mock_api.get(f"/v1/wallets/{_AID}").mock(
        return_value=httpx.Response(200, json={"agent_id": _AID, "balance_usd": "0"})
    )
    route = mock_api.post("/v1/wallets/topup").mock(
        return_value=httpx.Response(
            201,
            json={
                "agent_id": _AID,
                "amount_usd": "5",
                "new_balance_usd": "5",
                "ledger_entry_id": "le_1",
                "audit_event_id": "ae_1",
            },
        )
    )
    mock_api.get(f"/v1/agents/{_AID}").mock(
        return_value=httpx.Response(200, json=_agent_body())
    )
    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve(_AID)
    agent.wallet.topup(amount_usd=5)
    sent = route.calls.last.request
    body = json.loads(sent.content)
    assert body == {"agent_id": _AID, "amount_usd": "5"}


def test_inference_returns_response(mock_api: respx.MockRouter) -> None:
    mock_api.get(f"/v1/agents/{_AID}").mock(
        return_value=httpx.Response(200, json=_agent_body())
    )
    mock_api.post("/v1/inference").mock(
        return_value=httpx.Response(
            200,
            json={
                "inference_id": "inf_1",
                "receipt_id": "rcp_1",
                "content": "Hello!",
                "model_used": "claude-opus-4-7",
                "provider": "anthropic",
                "finish_reason": "stop",
                "finish_reason_native": "end_turn",
                "input_tokens": 5,
                "output_tokens": 2,
                "cost_usd": "0.0042",
            },
        )
    )
    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve(_AID)
    response = agent.inference(
        model="claude-opus-4-7",
        messages=[{"role": "user", "content": "Hi"}],
    )
    assert response.content == "Hello!"
    # text is the back-compat alias for content
    assert response.text == "Hello!"
    assert response.provider == "anthropic"
    assert response.finish_reason == "stop"
    assert response.finish_reason_native == "end_turn"
    assert float(response.cost_usd) == pytest.approx(0.0042)


def test_inference_body_carries_agent_id(mock_api: respx.MockRouter) -> None:
    mock_api.get(f"/v1/agents/{_AID}").mock(
        return_value=httpx.Response(200, json=_agent_body())
    )
    route = mock_api.post("/v1/inference").mock(
        return_value=httpx.Response(
            200,
            json={
                "inference_id": "inf_1",
                "receipt_id": "rcp_1",
                "content": "ok",
                "model_used": "claude-opus-4-7",
                "finish_reason": "stop",
                "input_tokens": 1,
                "output_tokens": 1,
                "cost_usd": "0.0",
            },
        )
    )
    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve(_AID)
    agent.inference(model="claude-opus-4-7", messages=[{"role": "user", "content": "x"}])
    sent = route.calls.last.request
    body = json.loads(sent.content)
    assert body["agent_id"] == _AID
    assert body["model"] == "claude-opus-4-7"


def test_inference_content_blocks_preserved(mock_api: respx.MockRouter) -> None:
    mock_api.get(f"/v1/agents/{_AID}").mock(
        return_value=httpx.Response(200, json=_agent_body())
    )
    mock_api.post("/v1/inference").mock(
        return_value=httpx.Response(
            200,
            json={
                "inference_id": "inf_1",
                "receipt_id": "rcp_1",
                "content": "Hello!",
                "content_blocks": [{"type": "text", "text": "Hello!"}],
                "model_used": "claude-opus-4-7",
                "finish_reason": "stop",
                "input_tokens": 1,
                "output_tokens": 1,
                "cost_usd": "0.0",
            },
        )
    )
    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve(_AID)
    response = agent.inference(model="claude-opus-4-7", messages=[])
    assert response.content_blocks == [{"type": "text", "text": "Hello!"}]


def test_inference_accepts_per_call_timeout(mock_api: respx.MockRouter) -> None:
    mock_api.get(f"/v1/agents/{_AID}").mock(
        return_value=httpx.Response(200, json=_agent_body())
    )
    route = mock_api.post("/v1/inference").mock(
        return_value=httpx.Response(
            200,
            json={
                "inference_id": "inf_1",
                "receipt_id": "rcp_1",
                "content": "ok",
                "model_used": "claude-opus-4-7",
                "finish_reason": "stop",
                "input_tokens": 1,
                "output_tokens": 1,
                "cost_usd": "0.0",
            },
        )
    )
    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve(_AID)
    response = agent.inference(model="claude-opus-4-7", messages=[], timeout=120.0)
    assert response.content == "ok"
    assert route.calls.last.request.extensions["timeout"]["read"] == 120.0


def test_audit_chain_events_and_verify(mock_api: respx.MockRouter) -> None:
    def make_event(seq: int, payload: dict[str, object], prev: str | None) -> dict[str, object]:
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

    e0 = make_event(0, {"v": 0}, None)
    e1 = make_event(1, {"v": 1}, str(e0["event_hash"]))
    e2 = make_event(2, {"v": 2}, str(e1["event_hash"]))

    mock_api.get(f"/v1/agents/{_AID}").mock(
        return_value=httpx.Response(200, json=_agent_body())
    )

    # Mock respects `since_seq` like the real API does — returns events with
    # seq > since_seq, empty when no more remain. Without this filtering,
    # the SDK pagination loop never terminates because every page returns
    # the same events.
    def handler(request: httpx.Request) -> httpx.Response:
        since_raw = request.url.params.get("since_seq")
        since = int(since_raw) if since_raw is not None else -1
        page = [e for e in [e0, e1, e2] if int(e["seq"]) > since]
        return httpx.Response(200, json={"agent_id": _AID, "events": page})

    mock_api.get(f"/v1/audit/{_AID}").mock(side_effect=handler)

    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve(_AID)
    events = list(agent.audit_chain.events(limit=10))
    assert len(events) == 3
    assert events[2].seq == 2
    assert agent.audit_chain.verify() is True


def test_audit_chain_paginates_via_since_seq(mock_api: respx.MockRouter) -> None:
    def make_event(seq: int, payload: dict[str, object], prev: str | None) -> dict[str, object]:
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

    e0 = make_event(0, {"v": 0}, None)
    e1 = make_event(1, {"v": 1}, str(e0["event_hash"]))
    e2 = make_event(2, {"v": 2}, str(e1["event_hash"]))

    mock_api.get(f"/v1/agents/{_AID}").mock(
        return_value=httpx.Response(200, json=_agent_body())
    )

    # Two-page walk: caller asks for limit=2 per page, gets e0+e1 on page 1,
    # then since_seq=1 returns e2 on page 2. The third call (since_seq=2)
    # returns empty and the walk terminates.
    pages = {
        "page1": [e0, e1],
        "page2": [e2],
        "page3": [],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        since = request.url.params.get("since_seq")
        if since is None:
            return httpx.Response(200, json={"agent_id": _AID, "events": pages["page1"]})
        if since == "1":
            return httpx.Response(200, json={"agent_id": _AID, "events": pages["page2"]})
        return httpx.Response(200, json={"agent_id": _AID, "events": pages["page3"]})

    mock_api.get(f"/v1/audit/{_AID}").mock(side_effect=handler)

    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve(_AID)
    # Force tiny page size so the test exercises the pagination path.
    # Without limit, the SDK pages at _PAGE_SIZE (500) which would return
    # all 3 events in one shot.
    events = list(agent.audit_chain.events(limit=3))
    assert [e.seq for e in events] == [0, 1, 2]


def test_audit_chain_limit_stops_before_next_page(mock_api: respx.MockRouter) -> None:
    def make_event(seq: int) -> dict[str, object]:
        return {
            "id": f"ev_{seq}",
            "agent_id": _AID,
            "seq": seq,
            "event_type": "test",
            "payload": {"v": seq},
            "previous_hash": None,
            "event_hash": "0" * 64,
            "created_at": datetime(2026, 5, 14, tzinfo=timezone.utc).isoformat(),
        }

    mock_api.get(f"/v1/agents/{_AID}").mock(
        return_value=httpx.Response(200, json=_agent_body())
    )
    page_one = mock_api.get(f"/v1/audit/{_AID}").mock(
        return_value=httpx.Response(
            200,
            json={"agent_id": _AID, "events": [make_event(0), make_event(1)]},
        )
    )

    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve(_AID)
    events = list(agent.audit_chain.events(limit=2))
    assert len(events) == 2
    # limit satisfied within page one — must not page again.
    assert page_one.call_count == 1


def test_audit_verify_remote(mock_api: respx.MockRouter) -> None:
    mock_api.get(f"/v1/agents/{_AID}").mock(
        return_value=httpx.Response(200, json=_agent_body())
    )
    mock_api.get(f"/v1/audit/{_AID}/verify").mock(
        return_value=httpx.Response(
            200,
            json={
                "agent_id": _AID,
                "event_count": 42,
                "valid": True,
                "failure_seq": None,
                "failure_reason": None,
            },
        )
    )
    client = AinferaClient(api_key="ak_test")
    agent = client.agents.retrieve(_AID)
    result = agent.audit_chain.verify_remote()
    assert result.valid is True
    assert result.event_count == 42


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
