"""AgentCard — JWS-signed identity card for an Agent.

Maps to Ontology v1.0 §2 AgentCard. The JWS is a compact serialization
(RFC 7515) over a JSON-LD payload that includes the Agent's public key,
trust hints, and capability metadata.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, PrivateAttr

from ainfera._internal.jws import verify_compact
from ainfera.exceptions import AgentCardInvalid

if TYPE_CHECKING:
    from ainfera.client import AinferaClient, AsyncAinferaClient


class AgentCard(BaseModel):
    """A signed identity card for an Agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    jws: str
    payload: dict[str, Any]
    kid: str

    _client: AinferaClient | None = PrivateAttr(default=None)
    _async_client: AsyncAinferaClient | None = PrivateAttr(default=None)

    def verify(self, public_key: bytes | str | None = None) -> bool:
        """Verify the JWS signature locally.

        If ``public_key`` is omitted, the Agent's pubkey is fetched from
        ``/v1/agents/{agent_id}/pubkey`` via the bound client.

        Args:
            public_key: PEM-encoded public key. When omitted, requires
                the AgentCard to have been retrieved through an
                :class:`AinferaClient` so the SDK can fetch the pubkey.

        Returns:
            ``True`` if the signature verifies.

        Raises:
            AgentCardInvalid: Signature does not verify, or no public key
                was provided and no bound client is available to fetch one.
        """
        key = public_key if public_key is not None else self._fetch_pubkey_sync()
        verified_payload = verify_compact(self.jws, key)
        if verified_payload != self.payload:
            raise AgentCardInvalid("verified JWS payload does not match card payload")
        return True

    async def averify(self, public_key: bytes | str | None = None) -> bool:
        """Async mirror of :meth:`verify`. Used with :class:`AsyncAinferaClient`."""
        key = public_key if public_key is not None else await self._fetch_pubkey_async()
        verified_payload = verify_compact(self.jws, key)
        if verified_payload != self.payload:
            raise AgentCardInvalid("verified JWS payload does not match card payload")
        return True

    def _fetch_pubkey_sync(self) -> bytes:
        if self._client is None:
            raise AgentCardInvalid(
                "no public_key provided and AgentCard is not bound to an AinferaClient; "
                "pass public_key explicitly or fetch the card via client.agents"
            )
        return self._client._fetch_agent_pubkey(self._agent_id_from_payload())

    async def _fetch_pubkey_async(self) -> bytes:
        if self._async_client is None:
            raise AgentCardInvalid(
                "no public_key provided and AgentCard is not bound to an AsyncAinferaClient; "
                "pass public_key explicitly or fetch the card via aclient.agents"
            )
        return await self._async_client._fetch_agent_pubkey(self._agent_id_from_payload())

    def _agent_id_from_payload(self) -> str:
        agent_id = self.payload.get("agent_id") or self.payload.get("sub")
        if not isinstance(agent_id, str):
            raise AgentCardInvalid("AgentCard payload missing agent_id/sub claim")
        return agent_id
