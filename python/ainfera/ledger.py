"""Ledger — append-only record of Wallet balance changes.

Maps to Ontology v1.0 §2 Ledger / LedgerEntry. SDK 1.1.0 (AIN-79) aligned
to ``GET /v1/ledger/{agent_id}`` which returns a ``LedgerView`` envelope
``{agent_id, balance_usd, entries: [...]}``. Pre-1.1.0 paths were against
``/v1/agents/{id}/wallet/ledger`` which doesn't exist in prod.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, PrivateAttr

from ainfera._internal import endpoints

if TYPE_CHECKING:
    from ainfera._internal.http import AsyncHttpClient, HttpClient


class LedgerEntry(BaseModel):
    """A single append-only Ledger entry."""

    id: str
    agent_id: str
    amount_usd: Decimal
    balance_after_usd: Decimal
    kind: str
    memo: str | None = None
    created_at: datetime


class Ledger(BaseModel):
    """The append-only Ledger for an Agent (sync flavor).

    Backed by ``GET /v1/ledger/{agent_id}`` which returns balance plus
    the entries list in one envelope. The SDK extracts ``entries`` for
    the caller; ``balance_usd`` is also accessible via :attr:`balance`.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_id: str

    _http: HttpClient | None = PrivateAttr(default=None)
    _last_balance: Decimal | None = PrivateAttr(default=None)

    def entries(self, *, limit: int = 100) -> list[LedgerEntry]:
        """Return up to ``limit`` Ledger entries, newest first."""
        body = self._require_http().request(
            "GET",
            endpoints.ledger(self.agent_id),
            params={"limit": limit},
        )
        self._last_balance = Decimal(str(body.get("balance_usd", "0")))
        return [LedgerEntry.model_validate(entry) for entry in body.get("entries", [])]

    @property
    def balance(self) -> Decimal | None:
        """Balance from the most recent :meth:`entries` call, ``None`` if never called."""
        return self._last_balance

    def _require_http(self) -> HttpClient:
        if self._http is None:
            raise RuntimeError("Ledger is not bound to a client")
        return self._http


class AsyncLedger(BaseModel):
    """The append-only Ledger for an Agent (async flavor)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_id: str

    _http: AsyncHttpClient | None = PrivateAttr(default=None)
    _last_balance: Decimal | None = PrivateAttr(default=None)

    async def entries(self, *, limit: int = 100) -> list[LedgerEntry]:
        """Return up to ``limit`` Ledger entries, newest first."""
        body = await self._require_http().request(
            "GET",
            endpoints.ledger(self.agent_id),
            params={"limit": limit},
        )
        self._last_balance = Decimal(str(body.get("balance_usd", "0")))
        return [LedgerEntry.model_validate(entry) for entry in body.get("entries", [])]

    @property
    def balance(self) -> Decimal | None:
        return self._last_balance

    def _require_http(self) -> AsyncHttpClient:
        if self._http is None:
            raise RuntimeError("AsyncLedger is not bound to a client")
        return self._http
