"""Tests for the JWS verification helper used by AgentCard.verify."""

from __future__ import annotations

import json

import pytest
from ainfera import AgentCard, AgentCardInvalid
from ainfera._internal.jws import verify_compact
from jose import jws

SECRET = "ainfera-test-secret-do-not-use-in-prod"


def _sign(payload: dict[str, object], alg: str = "HS256") -> str:
    return jws.sign(json.dumps(payload).encode("utf-8"), SECRET, algorithm=alg)


def test_verify_compact_happy_path() -> None:
    payload = {"agent_id": "ag_123", "kid": "k1", "iat": 1700000000}
    token = _sign(payload)
    assert verify_compact(token, SECRET) == payload


def test_verify_compact_rejects_tampered_payload() -> None:
    token = _sign({"agent_id": "ag_123"})
    header, _payload, signature = token.split(".")
    tampered = f"{header}.dGFtcGVyZWQ.{signature}"
    with pytest.raises(AgentCardInvalid):
        verify_compact(tampered, SECRET)


def test_verify_compact_rejects_wrong_key() -> None:
    token = _sign({"agent_id": "ag_123"})
    with pytest.raises(AgentCardInvalid):
        verify_compact(token, "wrong-secret")


def test_verify_compact_rejects_alg_none() -> None:
    # python-jose's `sign` won't emit `alg: none`, so we craft it manually.
    header = '{"alg":"none","typ":"JWT"}'
    body = '{"agent_id":"ag_pwned"}'
    import base64

    def b64(b: bytes) -> str:
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")

    token = f"{b64(header.encode())}.{b64(body.encode())}."
    with pytest.raises(AgentCardInvalid):
        verify_compact(token, SECRET)


def test_agent_card_verify_with_explicit_key() -> None:
    payload = {"agent_id": "ag_123", "kid": "k1"}
    token = _sign(payload)
    card = AgentCard(jws=token, payload=payload, kid="k1")
    assert card.verify(public_key=SECRET) is True


def test_agent_card_verify_rejects_mismatched_payload() -> None:
    signed_payload = {"agent_id": "ag_123"}
    token = _sign(signed_payload)
    # Card claims a different payload than what the JWS actually signed
    card = AgentCard(jws=token, payload={"agent_id": "ag_999"}, kid="k1")
    with pytest.raises(AgentCardInvalid):
        card.verify(public_key=SECRET)


def test_agent_card_verify_without_client_or_key_raises() -> None:
    payload = {"agent_id": "ag_123"}
    token = _sign(payload)
    card = AgentCard(jws=token, payload=payload, kid="k1")
    with pytest.raises(AgentCardInvalid, match="not bound"):
        card.verify()
