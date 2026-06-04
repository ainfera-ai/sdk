"""Top-level SDK clients.

:class:`AinferaClient` is the synchronous client; :class:`AsyncAinferaClient`
mirrors it for async callers. Both expose the same resource surface
(``client.agents``, ``client.receipts``).
"""

from __future__ import annotations

import os
from types import TracebackType

from ainfera._internal import endpoints
from ainfera._internal.http import AsyncHttpClient, HttpClient
from ainfera.agents import AgentsResource, AsyncAgentsResource, SignupResult
from ainfera.exceptions import AinferaError
from ainfera.receipt import Receipt

DEFAULT_BASE_URL = "https://api.ainfera.ai"
# 60s rather than 30s: long-context inference on large models routinely
# runs past 30s, and a too-tight default surfaces as a confusing SDK
# timeout rather than an honest "the model is still working" wait.
DEFAULT_TIMEOUT = 60.0
API_KEY_ENV_VAR = "AINFERA_API_KEY"


def _resolve_api_key(api_key: str | None) -> str:
    # An explicit empty string is the documented \"unauthenticated bootstrap\"
    # mode used to call the public POST /v1/agents/signup endpoint. None or
    # unset still falls back to the env var, then errors loudly if absent.
    if api_key == "":
        return ""
    resolved = api_key or os.environ.get(API_KEY_ENV_VAR)
    if not resolved:
        raise AinferaError(
            "No API key provided. Pass api_key= explicitly or set the "
            f"{API_KEY_ENV_VAR} environment variable."
        )
    return resolved


class ReceiptsResource:
    """Tenant-scoped collection of Receipts. Accessed via ``client.receipts``."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def retrieve(self, receipt_id: str) -> Receipt:
        """Receipt detail is embedded on each Inference response.

        The API does not expose ``GET /v1/receipts/{id}``; use
        ``agent.inference(...)`` and read ``response.receipt`` instead.
        """
        raise NotImplementedError(
            "Receipts are returned inline on inference responses; "
            "there is no GET /v1/receipts/{id} endpoint."
        )


class AsyncReceiptsResource:
    """Tenant-scoped collection of Receipts. Accessed via ``aclient.receipts``."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def retrieve(self, receipt_id: str) -> Receipt:
        """Receipt detail is embedded on each Inference response."""
        raise NotImplementedError(
            "Receipts are returned inline on inference responses; "
            "there is no GET /v1/receipts/{id} endpoint."
        )


class AinferaClient:
    """Synchronous Ainfera SDK client.

    Args:
        api_key: Tenant-level API key (``ainfera_*`` or ``ainfera_test_*``). If omitted,
            the SDK reads the ``AINFERA_API_KEY`` environment variable.
        base_url: Override for self-hosted deployments.
            Defaults to ``https://api.ainfera.ai``.
        timeout: HTTP timeout in seconds. Defaults to ``60``. Override
            per-call on long inference requests via ``agent.inference(timeout=...)``.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._http = HttpClient(
            base_url=base_url,
            api_key=_resolve_api_key(api_key),
            timeout=timeout,
        )
        self._agents = AgentsResource(self)
        self._receipts = ReceiptsResource(self._http)

    @classmethod
    def from_signup(
        cls,
        result: SignupResult,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> AinferaClient:
        """Build a client from a :class:`~ainfera.agents.SignupResult`."""
        return cls(api_key=result.api_key, base_url=base_url, timeout=timeout)

    @property
    def agents(self) -> AgentsResource:
        return self._agents

    @property
    def receipts(self) -> ReceiptsResource:
        return self._receipts

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> AinferaClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def _fetch_agent_pubkey(self, agent_id: str) -> bytes:
        """Fetch an Agent's Ed25519 public key (PEM) via the agent retrieve endpoint.

        SDK 1.1.0 (AIN-79): no dedicated ``/pubkey`` endpoint in prod — the
        pubkey is a field on the ``GET /v1/agents/{id}`` Agent response.
        """
        body = self._http.request("GET", endpoints.agent(agent_id))
        pem = body.get("public_key_ed25519")
        if not isinstance(pem, str) or not pem:
            raise AinferaError(
                f"Agent {agent_id} response is missing public_key_ed25519"
            )
        return pem.encode("utf-8")


class AsyncAinferaClient:
    """Asynchronous Ainfera SDK client. Mirrors :class:`AinferaClient`.

    Args:
        api_key: Tenant-level API key (``ainfera_*`` or ``ainfera_test_*``). If omitted,
            the SDK reads the ``AINFERA_API_KEY`` environment variable.
        base_url: Override for self-hosted deployments.
            Defaults to ``https://api.ainfera.ai``.
        timeout: HTTP timeout in seconds. Defaults to ``60``.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._http = AsyncHttpClient(
            base_url=base_url,
            api_key=_resolve_api_key(api_key),
            timeout=timeout,
        )
        self._agents = AsyncAgentsResource(self)
        self._receipts = AsyncReceiptsResource(self._http)

    @classmethod
    def from_signup(
        cls,
        result: SignupResult,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> AsyncAinferaClient:
        """Build a client from a :class:`~ainfera.agents.SignupResult`."""
        return cls(api_key=result.api_key, base_url=base_url, timeout=timeout)

    @property
    def agents(self) -> AsyncAgentsResource:
        return self._agents

    @property
    def receipts(self) -> AsyncReceiptsResource:
        return self._receipts

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> AsyncAinferaClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def _fetch_agent_pubkey(self, agent_id: str) -> bytes:
        """Fetch an Agent's Ed25519 public key (PEM) via the agent retrieve endpoint."""
        body = await self._http.request("GET", endpoints.agent(agent_id))
        pem = body.get("public_key_ed25519")
        if not isinstance(pem, str) or not pem:
            raise AinferaError(
                f"Agent {agent_id} response is missing public_key_ed25519"
            )
        return pem.encode("utf-8")
