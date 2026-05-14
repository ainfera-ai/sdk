"""Internal JWS sign/verify helpers (RFC 7515).

This module is the only place the SDK touches ``python-jose``. The
public surface is :func:`verify_compact`, used by :meth:`AgentCard.verify`.
"""

from __future__ import annotations

import json
from typing import Any

from jose import jws
from jose.exceptions import JOSEError

from ainfera.exceptions import AgentCardInvalid


def verify_compact(token: str, public_key: bytes | str) -> dict[str, Any]:
    """Verify a compact-serialization JWS and return its decoded payload.

    Args:
        token: The compact JWS string (``header.payload.signature``).
        public_key: PEM-encoded public key matching the JWS ``alg``.
            Accepts ``bytes`` or ``str``.

    Returns:
        The decoded payload as a Python ``dict``.

    Raises:
        AgentCardInvalid: Signature did not verify, or the payload was
            not valid JSON.
    """
    key = public_key.decode("utf-8") if isinstance(public_key, bytes) else public_key

    header = jws.get_unverified_header(token)
    alg = header.get("alg")
    if not alg or alg == "none":
        raise AgentCardInvalid(f"JWS header missing or insecure alg: {alg!r}")

    try:
        raw_payload = jws.verify(token, key, algorithms=[alg])
    except JOSEError as exc:
        raise AgentCardInvalid(f"JWS signature verification failed: {exc}") from exc

    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise AgentCardInvalid(f"JWS payload is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise AgentCardInvalid("JWS payload is not a JSON object")

    return payload
