"""Agent — the principal entity in Ainfera.

Maps to Ontology v1.0 §2 Agent. SDK 1.1.0 (AIN-79) realigned to the
production /v1/* surface; pre-D4 mock paths removed.

The Agent model binds against both the retrieve response (``id``,
``tenant_id``, ``name``, ``status``, ``public_key_ed25519``,
``created_at``) and the signup-bundle response (``agent_id``, ``name``).
The ``agent_id`` field aliases ``id`` so both shapes round-trip cleanly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, PrivateAttr

from ainfera._internal import endpoints
from ainfera.agent_card import AgentCard
from ainfera.audit import AsyncAuditChain, AuditChain
from ainfera.inference import InferenceResponse
from ainfera.wallet import AsyncWallet, Wallet

if TYPE_CHECKING:
    from ainfera._internal.http import AsyncHttpClient, HttpClient
    from ainfera.client import AinferaClient, AsyncAinferaClient


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
        Set ``model="ainfera-auto"`` to dispatch through L2 Routing.
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
            body = await http.request("GET", endpoints.wallet(self.agent_id))
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


class AgentsResource:
    """Tenant-scoped collection of Agents. Accessed via ``client.agents``.

    SDK 1.1.0 (AIN-79): ``register`` hits ``POST /v1/agents/register`` (was
    ``POST /v1/agents`` against pre-D4 mocks). The flat ``/v1/agents`` GET
    is not exposed in production; ``list()`` is dropped until the API
    surfaces it (tracked AIN-79 follow-up).
    """

    def __init__(self, client: AinferaClient) -> None:
        self._client = client
        self._http: HttpClient = client._http

    def register(self, *, tenant_id: str, name: str) -> Agent:
        """Register a new Agent under the given tenant.

        ``tenant_id`` is required by the API contract; multi-tenant users
        explicitly name the tenant. Single-tenant users typically use
        :meth:`signup` instead (follow-up — file under AIN-79).
        """
        body = self._http.request(
            "POST",
            endpoints.agent_register(),
            json={"tenant_id": tenant_id, "name": name},
        )
        return self._bind(body)

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

    async def retrieve(self, agent_id: str) -> AsyncAgent:
        """Retrieve an Agent by id."""
        body = await self._http.request("GET", endpoints.agent(agent_id))
        return self._bind(body)

    def _bind(self, body: dict[str, Any]) -> AsyncAgent:
        agent = AsyncAgent.model_validate(body)
        agent._client = self._client
        return agent
