"""Agent — the principal entity in Ainfera.

Maps to Ontology v1.0 §2 Agent. SDK 1.1.0 (AIN-79) realigned to the
production /v1/* surface; pre-D4 mock paths removed.

The Agent model binds against both the retrieve response (``id``,
``tenant_id``, ``name``, ``status``, ``public_key_ed25519``,
``created_at``) and the signup-bundle response (``agent_id``, ``name``).
The ``agent_id`` field aliases ``id`` so both shapes round-trip cleanly.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, PrivateAttr

from ainfera._internal import endpoints
from ainfera.agent_card import AgentCard
from ainfera.audit import AsyncAuditChain, AuditChain
from ainfera.inference import InferenceResponse
from ainfera.ledger import AsyncLedger, Ledger
from ainfera.wallet import AsyncWallet, Wallet

if TYPE_CHECKING:
    from ainfera._internal.http import AsyncHttpClient, HttpClient
    from ainfera.client import AinferaClient, AsyncAinferaClient


class _AsyncWalletRef:
    """Awaitable wallet handle for :class:`AsyncAgent`.

    Use ``wallet = await agent.wallet`` (not ``agent.wallet`` as a bare
    property like sync :class:`Agent`).
    """

    __slots__ = ("_agent",)

    def __init__(self, agent: AsyncAgent) -> None:
        self._agent = agent

    def __await__(self):
        return self._agent._fetch_wallet().__await__()

    async def topup(self, amount_usd: float | Decimal) -> AsyncWallet:
        wallet = await self
        return await wallet.topup(amount_usd=amount_usd)


class Agent(BaseModel):
    """An Ainfera Agent (sync flavor).

    Fields beyond ``agent_id`` + ``name`` are optional so the model
    round-trips both the slim signup-bundle and the full retrieve
    response without two separate types.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    agent_id: str = Field(validation_alias=AliasChoices("id", "agent_id"))
    name: str
    description: str | None = None
    tenant_id: str | None = None
    status: str | None = None
    public_key_ed25519: str | None = None

    _client: AinferaClient | None = PrivateAttr(default=None)
    _wallet: Wallet | None = PrivateAttr(default=None)
    _ledger: Ledger | None = PrivateAttr(default=None)
    _audit_chain: AuditChain | None = PrivateAttr(default=None)

    def refresh(self) -> Agent:
        """Refetch this Agent's data from the API and return ``self``."""
        http = self._require_client()._http
        body = http.request("GET", endpoints.agent(self.agent_id))
        fresh = Agent.model_validate(body)
        self.name = fresh.name
        self.description = fresh.description
        self.tenant_id = fresh.tenant_id
        self.status = fresh.status
        self.public_key_ed25519 = fresh.public_key_ed25519
        self._wallet = None
        self._ledger = None
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
            body = http.request("GET", endpoints.wallet(self.agent_id))
            wallet = Wallet.model_validate(body)
            wallet._http = http
            self._wallet = wallet
        return self._wallet

    @property
    def audit_chain(self) -> AuditChain:
        """The AuditChain for this Agent. Handle is cached; events fetched on demand."""
        if self._audit_chain is None:
            chain = AuditChain(agent_id=self.agent_id)
            chain._http = self._require_client()._http
            self._audit_chain = chain
        return self._audit_chain

    @property
    def ledger(self) -> Ledger:
        """The append-only Ledger for this Agent (``GET /v1/ledger/{agent_id}``)."""
        if self._ledger is None:
            book = Ledger(agent_id=self.agent_id)
            book._http = self._require_client()._http
            self._ledger = book
        return self._ledger

    def inference(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        timeout: float | None = None,
        **extra: Any,
    ) -> InferenceResponse:
        """Make a single Inference call routed through Ainfera.

        Hits flat ``POST /v1/inference``; agent_id travels in the body.
        Set ``model="ainfera-mithril"`` to dispatch through L2 Routing
        (the prime-brokerage default — let Ainfera pick the best route).
        ``"ainfera-auto"`` remains a silent alias for legacy callers.
        """
        payload: dict[str, Any] = {
            "agent_id": self.agent_id,
            "model": model,
            "messages": messages,
            **extra,
        }
        http = self._require_client()._http
        body = http.request(
            "POST",
            endpoints.inference(),
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

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    agent_id: str = Field(validation_alias=AliasChoices("id", "agent_id"))
    name: str
    description: str | None = None
    tenant_id: str | None = None
    status: str | None = None
    public_key_ed25519: str | None = None

    _client: AsyncAinferaClient | None = PrivateAttr(default=None)
    _wallet: AsyncWallet | None = PrivateAttr(default=None)
    _ledger: AsyncLedger | None = PrivateAttr(default=None)
    _audit_chain: AsyncAuditChain | None = PrivateAttr(default=None)

    async def refresh(self) -> AsyncAgent:
        """Refetch this Agent's data from the API and return ``self``."""
        http = self._require_client()._http
        body = await http.request("GET", endpoints.agent(self.agent_id))
        fresh = AsyncAgent.model_validate(body)
        self.name = fresh.name
        self.description = fresh.description
        self.tenant_id = fresh.tenant_id
        self.status = fresh.status
        self.public_key_ed25519 = fresh.public_key_ed25519
        self._wallet = None
        self._ledger = None
        self._audit_chain = None
        return self

    async def get_card(self) -> AgentCard:
        """Fetch this Agent's JWS-signed AgentCard."""
        http = self._require_client()._http
        body = await http.request("GET", endpoints.agent_card(self.agent_id))
        card = AgentCard.model_validate(body)
        card._async_client = self._client
        return card

    async def _fetch_wallet(self) -> AsyncWallet:
        """Load and cache the Wallet attached to this Agent."""
        if self._wallet is None:
            http = self._require_client()._http
            body = await http.request("GET", endpoints.wallet(self.agent_id))
            wallet = AsyncWallet.model_validate(body)
            wallet._http = http
            self._wallet = wallet
        return self._wallet

    async def get_wallet(self) -> AsyncWallet:
        """Fetch and cache the Wallet attached to this Agent."""
        return await self._fetch_wallet()

    @property
    def wallet(self) -> _AsyncWalletRef:
        """Awaitable wallet handle — ``w = await agent.wallet``."""
        return _AsyncWalletRef(self)

    @property
    def audit_chain(self) -> AsyncAuditChain:
        """The AuditChain handle. Events are fetched on demand."""
        if self._audit_chain is None:
            chain = AsyncAuditChain(agent_id=self.agent_id)
            chain._http = self._require_client()._http
            self._audit_chain = chain
        return self._audit_chain

    @property
    def ledger(self) -> AsyncLedger:
        """The append-only Ledger for this Agent (``GET /v1/ledger/{agent_id}``)."""
        if self._ledger is None:
            book = AsyncLedger(agent_id=self.agent_id)
            book._http = self._require_client()._http
            self._ledger = book
        return self._ledger

    async def inference(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        timeout: float | None = None,
        **extra: Any,
    ) -> InferenceResponse:
        """Make a single Inference call routed through Ainfera."""
        payload: dict[str, Any] = {
            "agent_id": self.agent_id,
            "model": model,
            "messages": messages,
            **extra,
        }
        http = self._require_client()._http
        body = await http.request(
            "POST",
            endpoints.inference(),
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


class SignupResult(BaseModel):
    """Bundle returned by ``POST /v1/agents/signup``.

    The signup endpoint provisions a Tenant + Agent + Wallet atomically and
    hands back a one-time API key alongside a JWS-signed AgentCard. Use
    this bundle to bootstrap a fresh client without an existing
    ``api_key``: the canonical pattern is
    ``client = AinferaClient.from_signup(result)``.

    ``api_key`` is shown once. Save it from this object before discarding.
    """

    model_config = ConfigDict(populate_by_name=True)

    agent_id: str = Field(validation_alias=AliasChoices("id", "agent_id"))
    agent_handle: str
    tenant_id: str
    owner_handle: str | None = None
    canonical_uri: str | None = None
    did_web: str | None = None
    api_key: str = Field(
        description="One-time API key — shown once; persist before discarding."
    )
    agent_card_jws: str | None = None

    @property
    def agent(self) -> Agent:
        """Return an unbound :class:`Agent` for the freshly-signed-up row.

        The Agent is **not bound to a client** — call
        ``AinferaClient(api_key=result.api_key).agents.retrieve(result.agent_id)``
        to operate on it, or use :meth:`AinferaClient.from_signup`.
        """
        return Agent(
            agent_id=self.agent_id,
            name=self.agent_handle,
            tenant_id=self.tenant_id,
        )


class AgentsResource:
    """Tenant-scoped collection of Agents. Accessed via ``client.agents``.

    SDK 1.1.0 (AIN-79): ``register`` hits ``POST /v1/agents/register`` (was
    ``POST /v1/agents`` against pre-D4 mocks). ``signup`` hits the public
    ``POST /v1/agents/signup`` bundle endpoint (Tenant + Agent + Wallet +
    one-time API key). The flat ``/v1/agents`` GET is not exposed in
    production; ``list()`` is dropped until the API surfaces it.
    """

    def __init__(self, client: AinferaClient) -> None:
        self._client = client
        self._http: HttpClient = client._http

    def register(self, *, tenant_id: str, name: str) -> Agent:
        """Register a new Agent under the given tenant.

        ``tenant_id`` is required by the API contract; multi-tenant users
        explicitly name the tenant. Single-tenant users typically use
        :meth:`signup` instead, which provisions the Tenant inline.
        """
        body = self._http.request(
            "POST",
            endpoints.agent_register(),
            json={"tenant_id": tenant_id, "name": name},
        )
        return self._bind(body)

    def signup(
        self,
        *,
        agent_handle: str,
        owner_handle: str | None = None,
        owner_source: str | None = None,
        owner_contact: str | None = None,
        per_call_cap_usd: str | float | None = None,
        daily_cap_usd: str | float | None = None,
        wallet_address: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SignupResult:
        """Provision a fresh Tenant + Agent + Wallet and return the bundle.

        The endpoint is public (no api_key required for this call). The
        returned ``SignupResult.api_key`` is shown once — persist it before
        discarding the result.

        Caps are passed as strings so decimal precision survives the wire.
        """
        payload: dict[str, Any] = {"agent_handle": agent_handle}
        if owner_handle is not None:
            payload["owner_handle"] = owner_handle
        if owner_source is not None:
            payload["owner_source"] = owner_source
        if owner_contact is not None:
            payload["owner_contact"] = owner_contact
        if per_call_cap_usd is not None:
            payload["per_call_cap_usd"] = str(per_call_cap_usd)
        if daily_cap_usd is not None:
            payload["daily_cap_usd"] = str(daily_cap_usd)
        if wallet_address is not None:
            payload["wallet_address"] = wallet_address
        if metadata is not None:
            payload["metadata"] = metadata
        body = self._http.request(
            "POST",
            endpoints.agent_signup(),
            json=payload,
        )
        return SignupResult.model_validate(body)

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

    async def register(self, *, tenant_id: str, name: str) -> AsyncAgent:
        """Register a new Agent under the given tenant."""
        body = await self._http.request(
            "POST",
            endpoints.agent_register(),
            json={"tenant_id": tenant_id, "name": name},
        )
        return self._bind(body)

    async def signup(
        self,
        *,
        agent_handle: str,
        owner_handle: str | None = None,
        owner_source: str | None = None,
        owner_contact: str | None = None,
        per_call_cap_usd: str | float | None = None,
        daily_cap_usd: str | float | None = None,
        wallet_address: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SignupResult:
        """Async twin of :meth:`AgentsResource.signup`."""
        payload: dict[str, Any] = {"agent_handle": agent_handle}
        if owner_handle is not None:
            payload["owner_handle"] = owner_handle
        if owner_source is not None:
            payload["owner_source"] = owner_source
        if owner_contact is not None:
            payload["owner_contact"] = owner_contact
        if per_call_cap_usd is not None:
            payload["per_call_cap_usd"] = str(per_call_cap_usd)
        if daily_cap_usd is not None:
            payload["daily_cap_usd"] = str(daily_cap_usd)
        if wallet_address is not None:
            payload["wallet_address"] = wallet_address
        if metadata is not None:
            payload["metadata"] = metadata
        body = await self._http.request(
            "POST",
            endpoints.agent_signup(),
            json=payload,
        )
        return SignupResult.model_validate(body)

    async def retrieve(self, agent_id: str) -> AsyncAgent:
        """Retrieve an Agent by id."""
        body = await self._http.request("GET", endpoints.agent(agent_id))
        return self._bind(body)

    def _bind(self, body: dict[str, Any]) -> AsyncAgent:
        agent = AsyncAgent.model_validate(body)
        agent._client = self._client
        return agent
