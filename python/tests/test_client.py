"""Smoke tests for the public SDK surface."""

from __future__ import annotations

import ainfera
import pytest
from ainfera import AinferaClient, AinferaError, AsyncAinferaClient, SignupResult


def test_version_is_set() -> None:
    assert isinstance(ainfera.__version__, str)
    assert ainfera.__version__ != ""


def test_public_exports_resolve() -> None:
    for name in ainfera.__all__:
        assert hasattr(ainfera, name), f"ainfera.{name} missing from public API"


def test_sync_client_constructs() -> None:
    client = AinferaClient(api_key="ak_test")
    try:
        assert client.agents is not None
        assert client.receipts is not None
    finally:
        client.close()


def test_async_client_constructs() -> None:
    client = AsyncAinferaClient(api_key="ak_test")
    assert client.agents is not None
    assert client.receipts is not None


def test_api_key_falls_back_to_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AINFERA_API_KEY", "ak_from_env")
    client = AinferaClient()
    try:
        assert client._http.api_key == "ak_from_env"
    finally:
        client.close()


def test_explicit_api_key_overrides_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AINFERA_API_KEY", "ak_from_env")
    client = AinferaClient(api_key="ak_explicit")
    try:
        assert client._http.api_key == "ak_explicit"
    finally:
        client.close()


def test_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AINFERA_API_KEY", raising=False)
    with pytest.raises(AinferaError, match="AINFERA_API_KEY"):
        AinferaClient()


def test_default_timeout_is_60s() -> None:
    client = AinferaClient(api_key="ak_test")
    try:
        assert client._http.timeout == 60.0
    finally:
        client.close()


def test_from_signup_builds_client() -> None:
    result = SignupResult.model_validate(
        {
            "agent_id": "ag_1",
            "agent_handle": "h",
            "tenant_id": "tn_1",
            "owner_handle": "o",
            "canonical_uri": "ainfera.ai/o/h",
            "did_web": "did:ainfera:agent:ag_1",
            "api_key": "ainfera_test_key",
            "agent_card_jws": "eyJhbGciOiJFZERTQSJ9.e30.e30",
        }
    )
    client = AinferaClient.from_signup(result)
    try:
        assert client._http.api_key == "ainfera_test_key"
    finally:
        client.close()
