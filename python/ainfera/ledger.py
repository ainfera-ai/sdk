"""Ledger — append-only record of Wallet balance changes.

Maps to Ontology v1.0 §2 Ledger / LedgerEntry. One LedgerEntry per
balance-changing event (topup, settlement, refund).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, PrivateAttr

from ainfera._internal import endpoints

if TYPE_CHECKING:
    from ainfera._internal.http import AsyncHttpClient, HttpClient


class LedgerEntry(BaseModel):
    """A single append-only Ledger entry."""

    entry_id: str
    wallet_id: str
    amount_usd: float
    balance_after_usd: float
    kind: str
    created_at: datetime


class Ledger(BaseModel):
    """The append-only Ledger for a Wallet (sync flavor)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    wallet_id: str
    agent_id: str

    _http: HttpClient | None = PrivateAttr(default=None)

    def entries(self, *, limit: int = 100) -> list[LedgerEntry]:
        """Return up to ``limit`` Ledger entries, newest first."""
        body = self._require_http().request(
            "GET",
            endpoints.agent_wallet_ledger(self.agent_id),
            params={"limit": limit},
        )
        return [LedgerEntry.model_validate(entry) for entry in body.get("data", [])]

    def _require_http(self) -> HttpClient:
        if self._http is None:
            raise RuntimeError("Ledger is not bound to a client")
        return self._http


class AsyncLedger(BaseModel):
    """The append-only Ledger for a Wallet (async flavor)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    wallet_id: str
    agent_id: str

    _http: AsyncHttpClient | None = PrivateAttr(default=None)

    async def entries(self, *, limit: int = 100) -> list[LedgerEntry]:
        """Return up to ``limit`` Ledger entries, newest first."""
        body = await self._require_http().request(
            "GET",
            endpoints.agent_wallet_ledger(self.agent_id),
            params={"limit": limit},
        )
        return [LedgerEntry.model_validate(entry) for entry in body.get("data", [])]

    def _require_http(self) -> AsyncHttpClient:
        if self._http is None:
            raise RuntimeError("AsyncLedger is not bound to a client")
        return self._http
