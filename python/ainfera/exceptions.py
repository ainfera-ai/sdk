"""Exception hierarchy for the Ainfera SDK.

All SDK errors inherit from :class:`AinferaError`. HTTP errors from the
Ainfera API surface as :class:`APIError` or one of its semantic subclasses
(:class:`ModelUnavailable`, :class:`WalletInsufficient`,
:class:`SpendPolicyExceeded`). Local verification failures surface as
:class:`AgentCardInvalid` or :class:`AuditChainBroken`.
"""

from __future__ import annotations

from typing import Any


class AinferaError(Exception):
    """Base exception for all SDK errors."""


class APIError(AinferaError):
    """Wrapper for HTTP errors returned by the Ainfera API."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body: dict[str, Any] = body or {}


class AgentCardInvalid(AinferaError):
    """JWS verification of an AgentCard failed."""


class ModelUnavailable(APIError):
    """422 — requested Model not available from any Provider."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 422,
        body: dict[str, Any] | None = None,
        model: str,
        provider: str | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, body=body)
        self.model = model
        self.provider = provider


class WalletInsufficient(APIError):
    """402 — Wallet balance below request cost."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 402,
        body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, body=body)


class SpendPolicyExceeded(APIError):
    """403 — Agent's spend policy blocked this Inference."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 403,
        body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, body=body)


class AuditChainBroken(AinferaError):
    """Local verification detected a hash chain break."""

    def __init__(self, message: str, *, broken_at_seq: int) -> None:
        super().__init__(message)
        self.broken_at_seq = broken_at_seq
