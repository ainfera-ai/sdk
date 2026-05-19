"""Wallet — prepaid balance attached to an Agent.

Maps to Ontology v1.0 §2 Wallet. SDK 1.1.0 (AIN-79) realigned to the
``/v1/wallets/{agent_id}`` + ``/v1/wallets/topup`` flat surface; the
prior ``/v1/agents/{id}/wallet`` paths did not exist in prod.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, PrivateAttr

from ainfera._internal import endpoints

if TYPE_CHECKING:
    from ainfera._internal.http import AsyncHttpClient, HttpClient


class Wallet(BaseModel):
    """Prepaid balance attached to an Agent (sync flavor).

    The API returns only ``{agent_id, balance_usd}`` — no separate wallet_id.
    Each Agent has exactly one Wallet, so the agent_id is the wallet's key.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_id: str
    balance_usd: Decimal

    _http: HttpClient | None = PrivateAttr(default=None)

    def topup(self, amount_usd: float | Decimal) -> Wallet:
        """Top up this Wallet by ``amount_usd`` and return the refreshed Wallet.

        Body carries ``agent_id`` per ``/v1/wallets/topup`` contract.
        Response is the L3 TopupResponse — the SDK extracts ``new_balance_usd``.
        """
        body = self._require_http().request(
            "POST",
            endpoints.wallet_topup(),
            json={"agent_id": self.agent_id, "amount_usd": str(amount_usd)},
        )
        self.balance_usd = Decimal(str(body["new_balance_usd"]))
        return self

    def _require_http(self) -> HttpClient:
        if self._http is None:
            raise RuntimeError(
                "Wallet is not bound to a client; retrieve it via agent.wallet"
            )
        return self._http


class AsyncWallet(BaseModel):
    """Prepaid balance attached to an Agent (async flavor)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_id: str
    balance_usd: Decimal

    _http: AsyncHttpClient | None = PrivateAttr(default=None)

    async def topup(self, amount_usd: float | Decimal) -> AsyncWallet:
        """Top up this Wallet by ``amount_usd`` and return the refreshed Wallet."""
        body = await self._require_http().request(
            "POST",
            endpoints.wallet_topup(),
            json={"agent_id": self.agent_id, "amount_usd": str(amount_usd)},
        )
        self.balance_usd = Decimal(str(body["new_balance_usd"]))
        return self

    def _require_http(self) -> AsyncHttpClient:
        if self._http is None:
            raise RuntimeError(
                "AsyncWallet is not bound to a client; retrieve it via agent.wallet"
            )
        return self._http
