"""Wallet — prepaid balance attached to an Agent.

Maps to Ontology v1.0 §2 Wallet. D9 ships prepaid topup; D14+ adds x402
USDC topup as a second funding path.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, PrivateAttr

from ainfera._internal import endpoints

if TYPE_CHECKING:
    from ainfera._internal.http import AsyncHttpClient, HttpClient


class Wallet(BaseModel):
    """Prepaid balance attached to an Agent (sync flavor)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    wallet_id: str
    agent_id: str
    balance_usd: float

    _http: HttpClient | None = PrivateAttr(default=None)

    def topup(self, amount_usd: float) -> Wallet:
        """Top up this Wallet by ``amount_usd`` and return the refreshed Wallet."""
        body = self._require_http().request(
            "POST",
            endpoints.agent_wallet_topup(self.agent_id),
            json={"amount_usd": amount_usd},
        )
        self.balance_usd = float(body["balance_usd"])
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

    wallet_id: str
    agent_id: str
    balance_usd: float

    _http: AsyncHttpClient | None = PrivateAttr(default=None)

    async def topup(self, amount_usd: float) -> AsyncWallet:
        """Top up this Wallet by ``amount_usd`` and return the refreshed Wallet."""
        body = await self._require_http().request(
            "POST",
            endpoints.agent_wallet_topup(self.agent_id),
            json={"amount_usd": amount_usd},
        )
        self.balance_usd = float(body["balance_usd"])
        return self

    def _require_http(self) -> AsyncHttpClient:
        if self._http is None:
            raise RuntimeError(
                "AsyncWallet is not bound to a client; retrieve it via agent.wallet"
            )
        return self._http
