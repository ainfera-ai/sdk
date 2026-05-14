"""Canonical JSON encoding for hash-chain verification.

The Ainfera AuditChain rule is::

    event_hash = sha256(previous_hash + canonical_json(payload))

Canonical JSON here means: sorted keys, no whitespace, UTF-8, separators
``(',', ':')``. This matches the encoding the Ainfera control plane
applies when signing events, so a customer running ``AuditChain.verify``
locally arrives at the same bytes the control plane hashed.
"""

from __future__ import annotations

import json
from typing import Any


def canonical_json(payload: Any) -> bytes:
    """Encode ``payload`` as canonical JSON bytes.

    Args:
        payload: A JSON-serializable value (dict, list, str, int, float,
            bool, None). ``ensure_ascii=False`` so non-ASCII strings are
            emitted as UTF-8 rather than ``\\uXXXX`` escapes.
    """
    return json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
