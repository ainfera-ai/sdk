"""Tests for the HTTP transport's status-code-to-exception mapping."""

from __future__ import annotations

import httpx
import pytest
import respx
from ainfera import (
    AinferaClient,
    APIError,
    ModelUnavailable,
    SpendPolicyExceeded,
    WalletInsufficient,
)


def test_402_maps_to_wallet_insufficient(mock_api: respx.MockRouter) -> None:
    mock_api.post("/v1/inference").mock(
        return_value=httpx.Response(402, json={"message": "balance below cost"})
    )
    client = AinferaClient(api_key="ak_test")
    agent = _bare_agent(client, "ag_x")
    with pytest.raises(WalletInsufficient):
        agent.inference(model="x", messages=[{"role": "user", "content": "hi"}])


def test_403_maps_to_spend_policy_exceeded(mock_api: respx.MockRouter) -> None:
    mock_api.post("/v1/inference").mock(
        return_value=httpx.Response(
            403,
            json={
                "code": "spend_policy_exceeded",
                "error": "spend_policy_exceeded",
                "message": "policy blocked",
            },
        )
    )
    client = AinferaClient(api_key="ak_test")
    agent = _bare_agent(client, "ag_x")
    with pytest.raises(SpendPolicyExceeded):
        agent.inference(model="x", messages=[])


def test_403_without_spend_code_maps_to_api_error(mock_api: respx.MockRouter) -> None:
    mock_api.post("/v1/inference").mock(
        return_value=httpx.Response(403, json={"detail": "agent belongs to another tenant"})
    )
    client = AinferaClient(api_key="ak_test")
    agent = _bare_agent(client, "ag_x")
    with pytest.raises(APIError) as exc:
        agent.inference(model="x", messages=[])
    assert exc.value.status_code == 403


def test_422_model_unavailable_carries_model_and_provider(
    mock_api: respx.MockRouter,
) -> None:
    mock_api.post("/v1/inference").mock(
        return_value=httpx.Response(
            422,
            json={
                "error": "model_unavailable",
                "message": "gpt-9.0 not available",
                "model": "gpt-9.0",
                "provider": "openai",
            },
        )
    )
    client = AinferaClient(api_key="ak_test")
    agent = _bare_agent(client, "ag_x")
    with pytest.raises(ModelUnavailable) as exc:
        agent.inference(model="gpt-9.0", messages=[])
    assert exc.value.model == "gpt-9.0"
    assert exc.value.provider == "openai"


def test_500_maps_to_generic_api_error(mock_api: respx.MockRouter) -> None:
    mock_api.post("/v1/inference").mock(return_value=httpx.Response(500, json={"message": "boom"}))
    client = AinferaClient(api_key="ak_test")
    agent = _bare_agent(client, "ag_x")
    with pytest.raises(APIError) as exc:
        agent.inference(model="x", messages=[])
    assert exc.value.status_code == 500


def test_bearer_header_sent(mock_api: respx.MockRouter) -> None:
    route = mock_api.get("/v1/agents/ag_x").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "ag_x",
                "tenant_id": "tn_1",
                "name": "n",
                "status": "active",
                "public_key_ed25519": "PEM",
                "created_at": "2026-05-14T00:00:00Z",
            },
        )
    )
    client = AinferaClient(api_key="ak_secret")
    client.agents.retrieve("ag_x")
    sent = route.calls.last.request
    assert sent.headers["Authorization"] == "Bearer ak_secret"
    assert "ainfera-python/" in sent.headers["User-Agent"]


def _bare_agent(client: AinferaClient, agent_id: str) -> object:
    from ainfera.agents import Agent

    agent = Agent(agent_id=agent_id, name="x")
    agent._client = client
    return agent
