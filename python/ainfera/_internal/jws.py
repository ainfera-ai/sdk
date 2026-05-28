"""Internal JWS sign/verify helpers (RFC 7515).

AIN-269 swap: this module is the only place the SDK touches a JOSE
library. We use ``joserfc`` (not ``python-jose``) to drop
GHSA-wj6h-64fc-37mp. The public surface is :func:`verify_compact`,
used by :meth:`AgentCard.verify`.
"""

from __future__ import annotations

import json
from typing import Any

from joserfc import jws
from joserfc.errors import JoseError
from joserfc.jwk import ECKey, OctKey, OKPKey, RSAKey

from ainfera.exceptions import AgentCardInvalid

# Algorithms the SDK is willing to verify. EdDSA is the production path
# (Ed25519 AgentCards from the api). HS256 is the test path. Everything
# else is opt-in via a future revision.
_ALLOWED_ALGS = frozenset({"EdDSA", "HS256", "ES256", "RS256"})


def _import_key_for_alg(key_data: str | bytes, alg: str) -> Any:
    """Return a joserfc Key instance appropriate for ``alg``.

    For HMAC algs (HS*) the key_data is a shared secret (string/bytes).
    For asymmetric algs (EdDSA / ES* / RS*) the key_data is a PEM-encoded
    public key.
    """
    if alg.startswith("HS"):
        return OctKey.import_key(key_data)
    if alg == "EdDSA":
        return OKPKey.import_key(key_data)
    if alg.startswith("ES"):
        return ECKey.import_key(key_data)
    if alg.startswith(("RS", "PS")):
        return RSAKey.import_key(key_data)
    raise AgentCardInvalid(f"Unsupported JWS alg: {alg!r}")


def verify_compact(token: str, public_key: bytes | str) -> dict[str, Any]:
    """Verify a compact-serialization JWS and return its decoded payload.

    Args:
        token: The compact JWS string (``header.payload.signature``).
        public_key: PEM-encoded public key matching the JWS ``alg``.
            Accepts ``bytes`` or ``str``.

    Returns:
        The decoded payload as a Python ``dict``.

    Raises:
        AgentCardInvalid: Signature did not verify, the alg was rejected,
            or the payload was not valid JSON.
    """
    key_material = (
        public_key.decode("utf-8") if isinstance(public_key, bytes) else public_key
    )

    try:
        sig_unverified = jws.extract_compact(token.encode("ascii"))
    except (JoseError, ValueError) as exc:
        raise AgentCardInvalid(f"JWS is not a valid compact serialization: {exc}") from exc

    header = sig_unverified.protected or {}
    alg = header.get("alg")
    if not alg or alg == "none" or alg not in _ALLOWED_ALGS:
        raise AgentCardInvalid(f"JWS header missing or insecure alg: {alg!r}")

    try:
        key = _import_key_for_alg(key_material, alg)
        sig = jws.deserialize_compact(token, key, algorithms=[alg])
    except JoseError as exc:
        raise AgentCardInvalid(f"JWS signature verification failed: {exc}") from exc

    try:
        payload = json.loads(sig.payload)
    except json.JSONDecodeError as exc:
        raise AgentCardInvalid(f"JWS payload is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise AgentCardInvalid("JWS payload is not a JSON object")

    return payload
