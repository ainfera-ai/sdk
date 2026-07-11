"""Tests for the offline hash-chain verification primitives.

These verify the customer-trust contract: an auditor can hand-compute
``event_hash = sha256(previous_hash + canonical_json(payload))`` and
arrive at the same result the Ainfera control plane produced.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

import pytest
from ainfera import AuditChainBroken, AuditEvent, verify_chain, verify_event_hash
from ainfera._internal.canonical import canonical_json


def _build_event(
    *,
    seq: int,
    event_type: str,
    payload: dict[str, Any],
    previous_hash: str | None,
) -> AuditEvent:
    hasher = hashlib.sha256()
    hasher.update((previous_hash or "").encode("utf-8"))
    hasher.update(canonical_json(payload))
    return AuditEvent(
        event_id=f"ev_{seq}",
        agent_id="ag_test",
        seq=seq,
        event_type=event_type,
        payload=payload,
        previous_hash=previous_hash,
        event_hash=hasher.hexdigest(),
        created_at=datetime(2026, 5, 14, 10, 0, seq, tzinfo=timezone.utc),
    )


def test_canonical_json_sorts_keys() -> None:
    assert canonical_json({"b": 1, "a": 2}) == b'{"a":2,"b":1}'


def test_canonical_json_no_whitespace() -> None:
    assert canonical_json({"a": [1, 2, 3]}) == b'{"a":[1,2,3]}'


def test_canonical_json_unicode_preserved() -> None:
    assert canonical_json({"name": "Ælfred"}) == '{"name":"Ælfred"}'.encode()


def test_verify_event_hash_happy_path() -> None:
    event = _build_event(
        seq=0,
        event_type="agent.registered",
        payload={"name": "test"},
        previous_hash=None,
    )
    assert verify_event_hash(event, previous_hash=None) is True


def test_verify_event_hash_detects_payload_tamper() -> None:
    event = _build_event(
        seq=0,
        event_type="agent.registered",
        payload={"name": "test"},
        previous_hash=None,
    )
    tampered = event.model_copy(update={"payload": {"name": "TAMPERED"}})
    assert verify_event_hash(tampered, previous_hash=None) is False


def test_verify_chain_three_events_intact() -> None:
    e0 = _build_event(seq=0, event_type="registered", payload={"x": 1}, previous_hash=None)
    e1 = _build_event(seq=1, event_type="inference", payload={"x": 2}, previous_hash=e0.event_hash)
    e2 = _build_event(seq=2, event_type="topup", payload={"x": 3}, previous_hash=e1.event_hash)
    assert verify_chain([e0, e1, e2]) is True


def test_verify_chain_empty_raises() -> None:
    with pytest.raises(AuditChainBroken) as exc:
        verify_chain([])
    assert exc.value.broken_at_seq == 0


def test_verify_chain_detects_broken_hash() -> None:
    e0 = _build_event(seq=0, event_type="x", payload={"v": 0}, previous_hash=None)
    e1 = _build_event(seq=1, event_type="x", payload={"v": 1}, previous_hash=e0.event_hash)
    e1_tampered = e1.model_copy(update={"event_hash": "0" * 64})
    with pytest.raises(AuditChainBroken) as exc:
        verify_chain([e0, e1_tampered])
    assert exc.value.broken_at_seq == 1


def test_verify_chain_detects_previous_hash_mismatch() -> None:
    e0 = _build_event(seq=0, event_type="x", payload={"v": 0}, previous_hash=None)
    e1 = _build_event(seq=1, event_type="x", payload={"v": 1}, previous_hash="deadbeef" * 8)
    with pytest.raises(AuditChainBroken) as exc:
        verify_chain([e0, e1])
    assert exc.value.broken_at_seq == 1


def test_audit_event_accepts_prev_hash_alias() -> None:
    event = AuditEvent.model_validate(
        {
            "agent_id": "ag_test",
            "seq": 0,
            "event_type": "agent.registered",
            "payload": {"x": 1},
            "prev_hash": None,
            "event_hash": "a" * 64,
            "created_at": "2026-05-14T10:00:00Z",
        }
    )
    assert event.previous_hash is None


def test_verify_chain_detects_seq_gap() -> None:
    e0 = _build_event(seq=0, event_type="x", payload={"v": 0}, previous_hash=None)
    e2 = _build_event(seq=2, event_type="x", payload={"v": 2}, previous_hash=e0.event_hash)
    with pytest.raises(AuditChainBroken) as exc:
        verify_chain([e0, e2])
    assert exc.value.broken_at_seq == 2
