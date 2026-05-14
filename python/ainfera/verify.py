"""Local hash-chain verification helpers.

Pure-stdlib, offline. These functions are the customer-trust primitive:
an Annex IV auditor can verify an AuditChain without trusting Ainfera —
hand them the events plus this code and they can confirm tamper-evidence
themselves.

The chain rule (Ontology v1.0 §2 AuditEvent)::

    event_hash = sha256_hex(
        (previous_hash or "") + canonical_json(payload)
    )

The first event in a chain has ``previous_hash = None``; the hash input
treats that as an empty string so the rule is uniform across the chain.
"""

from __future__ import annotations

import hashlib

from ainfera._internal.canonical import canonical_json
from ainfera.audit import AuditEvent
from ainfera.exceptions import AuditChainBroken


def _expected_hash(payload: object, previous_hash: str | None) -> str:
    hasher = hashlib.sha256()
    hasher.update((previous_hash or "").encode("utf-8"))
    hasher.update(canonical_json(payload))
    return hasher.hexdigest()


def verify_event_hash(event: AuditEvent, previous_hash: str | None) -> bool:
    """Verify a single AuditEvent's ``event_hash`` matches the chain rule.

    Returns ``True`` on match, ``False`` on mismatch. Does not raise — use
    :func:`verify_chain` when you want a broken link to surface as an
    :class:`ainfera.AuditChainBroken` exception.
    """
    return event.event_hash == _expected_hash(event.payload, previous_hash)


def verify_chain(events: list[AuditEvent]) -> bool:
    """Verify a full ordered list of AuditEvents.

    Events must be ordered by ``seq`` ascending and contiguous. Returns
    ``True`` if every link checks out. Raises :class:`ainfera.AuditChainBroken`
    at the first broken link (mismatched hash or non-contiguous ``seq`` /
    ``previous_hash``) with ``broken_at_seq`` set.
    """
    previous_hash: str | None = None
    expected_seq = events[0].seq if events else 0

    for event in events:
        if event.seq != expected_seq:
            raise AuditChainBroken(
                f"non-contiguous seq: expected {expected_seq}, got {event.seq}",
                broken_at_seq=event.seq,
            )
        if event.previous_hash != previous_hash:
            raise AuditChainBroken(
                f"previous_hash mismatch at seq {event.seq}",
                broken_at_seq=event.seq,
            )
        if not verify_event_hash(event, previous_hash):
            raise AuditChainBroken(
                f"event_hash mismatch at seq {event.seq}",
                broken_at_seq=event.seq,
            )
        previous_hash = event.event_hash
        expected_seq += 1

    return True
