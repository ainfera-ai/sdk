"""Agent — the principal entity in Ainfera.

Maps to Ontology v1.0 §2 Agent. Once registered, the Agent object is the
handle for everything that follows: AgentCard, Wallet, Inference,
AuditChain. Methods are scoped here (``agent.inference(...)``) rather
than on the top-level client to keep the per-operation line count low.

This module hosts both flavors: :class:`Agent` for use with
:class:`ainfera.AinferaClient`, and :class:`AsyncAgent` for use with
:class:`ainfera.AsyncAinferaClient`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, PrivateAttr

from ainfera._internal import endpoints
from ainfera.agent_card import AgentCard
from ainfera.audit import AsyncAuditChain, AuditChain
from ainfera.inference import InferenceResponse
from ainfera.wallet import AsyncWallet, Wallet

if TYPE_CHECKING:
    from ainfera._internal.http import AsyncHttpClient, HttpClient
    from ainfera.client import AinferaClient, AsyncAinferaClient


class Agent(BaseModel):
    """An Ainfera Agent (sync flavor)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_id: str
    name: str
    description: str | None = None

    _client: AinferaClient | None = PrivateAttr(default=None)
    _wallet: Wallet | None = PrivateAttr(default=None)
    _audit_chain: AuditChain | None = PrivateAttr(default=None)

    def refresh(self) -> Agent:
        """Refetch this Agent's data from the API and return ``self``.

        Updates mutable fields in place and drops the cached Wallet and
        AuditChain handles so the next access re-fetches them.
        """
        http = self._require_client()._http
        body = http.request("GET", endpoints.agent(self.agent_id))
        fresh = Agent.model_validate(body)
        self.name = fresh.name
        self.description = fresh.description
        self._wallet = None
        self._audit_chain = None
        return self

    def get_card(self) -> AgentCard:
        """Fetch this Agent's JWS-signed AgentCard."""
        http = self._require_client()._http
        body = http.request("GET", endpoints.agent_card(self.agent_id))
        card = AgentCard.model_validate(body)
        card._client = self._client
        return card

    @property
    def wallet(self) -> Wallet:
        """The Wallet attached to this Agent. Fetched once and cached."""
        if self._wallet is None:
            http = self._require_client()._http
            body = http.request("GET", endpoints.agent_wallet(self.agent_id))
            wallet = Wallet.model_validate(body)
            wallet._http = http
            self._wallet = wallet
        return self._wallet

    @property
    def audit_chain(self) -> AuditChain:
        """The AuditChain for this Agent. Handle is cached; events are fetched on demand."""
        if self._audit_chain is None:
            chain = AuditChain(agent_id=self.agent_id)
            chain._http = self._require_client()._http
            self._audit_chain = chain
        return self._audit_chain

    def inference(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        timeout: float | None = None,
        **extra: Any,
    ) -> InferenceResponse:
        """Make a single Inference call routed through Ainfera.

        Args:
            model: Model identifier to route to.
            messages: Chat messages in the standard role/content shape.
            timeout: Per-call HTTP timeout in seconds. Overrides the
                client default for this request only — raise it for
                long-context calls on large models.
            **extra: Additional request fields passed through verbatim.
        """
        payload: dict[str, Any] = {"model": model, "messages": messages, **extra}
        http = self._require_client()._http
        body = http.request(
            "POST",
            endpoints.agent_inference(self.agent_id),
            json=payload,
            timeout=timeout,
        )
        return InferenceResponse.model_validate(body)

    def _require_client(self) -> AinferaClient:
        if self._client is None:
            raise RuntimeError(
                "Agent is not bound to a client; retrieve it via client.agents"
            )
        return self._client


class AsyncAgent(BaseModel):
    """An Ainfera Agent (async flavor)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_id: str
    name: str
    description: str | None = None

    _client: AsyncAinferaClient | None = PrivateAttr(default=None)
    _wallet: AsyncWallet | None = PrivateAttr(default=None)
    _audit_chain: AsyncAuditChain | None = PrivateAttr(default=None)

    async def refresh(self) -> AsyncAgent:
        """Refetch this Agent's data from the API and return ``self``.

        Updates mutable fields in place and drops the cached Wallet and
        AuditChain handles so the next access re-fetches them.
        """
        http = self._require_client()._http
        body = await http.request("GET", endpoints.agent(self.agent_id))
        fresh = AsyncAgent.model_validate(body)
        self.name = fresh.name
        self.description = fresh.description
        self._wallet = None
        self._audit_chain = None
        return self

    async def get_card(self) -> AgentCard:
        """Fetch this Agent's JWS-signed AgentCard."""
        http = self._require_client()._http
        body = await http.request("GET", endpoints.agent_card(self.agent_id))
        card = AgentCard.model_validate(body)
        card._async_client = self._client
        return card

    async def wallet(self) -> AsyncWallet:
        """Fetch and cache the Wallet attached to this Agent."""
        if self._wallet is None:
            http = self._require_client()._http
            body = await http.request("GET", endpoints.agent_wallet(self.agent_id))
            wallet = AsyncWallet.model_validate(body)
            wallet._http = http
            self._wallet = wallet
        return self._wallet

    @property
    def audit_chain(self) -> AsyncAuditChain:
        """The AuditChain handle. Events are fetched on demand."""
        if self._audit_chain is None:
            chain = AsyncAuditChain(agent_id=self.agent_id)
            chain._http = self._require_client()._http
            self._audit_chain = chain
        return self._audit_chain

    async def inference(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        timeout: float | None = None,
        **extra: Any,
    ) -> InferenceResponse:
        """Make a single Inference call routed through Ainfera.

        Args:
            model: Model identifier to route to.
            messages: Chat messages in the standard role/content shape.
            timeout: Per-call HTTP timeout in seconds. Overrides the
                client default for this request only.
            **extra: Additional request fields passed through verbatim.
        """
        payload: dict[str, Any] = {"model": model, "messages": messages, **extra}
        http = self._require_client()._http
        body = await http.request(
            "POST",
            endpoints.agent_inference(self.agent_id),
            json=payload,
            timeout=timeout,
        )
        return InferenceResponse.model_validate(body)

    def _require_client(self) -> AsyncAinferaClient:
        if self._client is None:
            raise RuntimeError(
                "AsyncAgent is not bound to a client; retrieve it via aclient.agents"
            )
        return self._client


class AgentsResource:
    """Tenant-scoped collection of Agents. Accessed via ``client.agents``."""

    def __init__(self, client: AinferaClient) -> None:
        self._client = client
        self._http: HttpClient = client._http

    def register(self, *, name: str, description: str | None = None) -> Agent:
        """Register a new Agent under the calling tenant."""
        body = self._http.request(
            "POST",
            endpoints.agents_collection(),
            json={"name": name, "description": description},
        )
        return self._bind(body)

    def list(self, *, limit: int = 100) -> list[Agent]:
        """List Agents under the calling tenant, newest first."""
        body = self._http.request(
            "GET",
            endpoints.agents_collection(),
            params={"limit": limit},
        )
        return [self._bind(raw) for raw in body.get("data", [])]

    def retrieve(self, agent_id: str) -> Agent:
        """Retrieve an Agent by id."""
        body = self._http.request("GET", endpoints.agent(agent_id))
        return self._bind(body)

    def _bind(self, body: dict[str, Any]) -> Agent:
        agent = Agent.model_validate(body)
        agent._client = self._client
        return agent


class AsyncAgentsResource:
    """Tenant-scoped collection of Agents. Accessed via ``aclient.agents``."""

    def __init__(self, client: AsyncAinferaClient) -> None:
        self._client = client
        self._http: AsyncHttpClient = client._http

    async def register(self, *, name: str, description: str | None = None) -> AsyncAgent:
        """Register a new Agent under the calling tenant."""
        body = await self._http.request(
            "POST",
            endpoints.agents_collection(),
            json={"name": name, "description": description},
        )
        return self._bind(body)

    async def list(self, *, limit: int = 100) -> list[AsyncAgent]:
        """List Agents under the calling tenant, newest first."""
        body = await self._http.request(
            "GET",
            endpoints.agents_collection(),
            params={"limit": limit},
        )
        return [self._bind(raw) for raw in body.get("data", [])]

    async def retrieve(self, agent_id: str) -> AsyncAgent:
        """Retrieve an Agent by id."""
        body = await self._http.request("GET", endpoints.agent(agent_id))
        return self._bind(body)

    def _bind(self, body: dict[str, Any]) -> AsyncAgent:
        agent = AsyncAgent.model_validate(body)
        agent._client = self._client
        return agent
