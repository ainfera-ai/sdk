"""Internal httpx wrappers.

Two classes — :class:`HttpClient` (sync) and :class:`AsyncHttpClient`
(async) — share the same error-mapping rules. Status code ↦ exception:

================  ===============================
HTTP status       Exception
================  ===============================
402               :class:`ainfera.WalletInsufficient`
403               :class:`ainfera.SpendPolicyExceeded`
422 model-related :class:`ainfera.ModelUnavailable`
Other 4xx/5xx     :class:`ainfera.APIError`
================  ===============================
"""

from __future__ import annotations

from typing import Any

import httpx

from ainfera._version import __version__
from ainfera.exceptions import (
    APIError,
    ModelUnavailable,
    SpendPolicyExceeded,
    WalletInsufficient,
)


def _user_agent() -> str:
    return f"ainfera-python/{__version__} httpx/{httpx.__version__}"


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": _user_agent(),
        "Accept": "application/json",
    }


def _parse_body(response: httpx.Response) -> dict[str, Any]:
    try:
        body = response.json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


def _map_error(response: httpx.Response) -> APIError:
    body = _parse_body(response)
    message = body.get("message") or body.get("error") or response.reason_phrase or "API error"
    status = response.status_code

    if status == 402:
        return WalletInsufficient(message, body=body)
    if status == 403:
        return SpendPolicyExceeded(message, body=body)
    if status == 422:
        kind = body.get("error") or body.get("code")
        if kind == "model_unavailable":
            return ModelUnavailable(
                message,
                body=body,
                model=body.get("model", ""),
                provider=body.get("provider"),
            )
    return APIError(message, status_code=status, body=body)


class HttpClient:
    """Sync httpx wrapper used by :class:`ainfera.AinferaClient`."""

    def __init__(self, base_url: str, api_key: str, timeout: float) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers=_headers(api_key),
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        timeout_arg = timeout if timeout is not None else httpx.USE_CLIENT_DEFAULT
        response = self._client.request(
            method, path, json=json, params=params, timeout=timeout_arg
        )
        if response.status_code >= 400:
            raise _map_error(response)
        return _parse_body(response)

    def get_bytes(self, path: str) -> bytes:
        """Fetch a raw byte payload (e.g. a PEM-encoded pubkey)."""
        response = self._client.request("GET", path)
        if response.status_code >= 400:
            raise _map_error(response)
        return response.content

    def close(self) -> None:
        self._client.close()


class AsyncHttpClient:
    """Async httpx wrapper used by :class:`ainfera.AsyncAinferaClient`."""

    def __init__(self, base_url: str, api_key: str, timeout: float) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers=_headers(api_key),
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        timeout_arg = timeout if timeout is not None else httpx.USE_CLIENT_DEFAULT
        response = await self._client.request(
            method, path, json=json, params=params, timeout=timeout_arg
        )
        if response.status_code >= 400:
            raise _map_error(response)
        return _parse_body(response)

    async def get_bytes(self, path: str) -> bytes:
        response = await self._client.request("GET", path)
        if response.status_code >= 400:
            raise _map_error(response)
        return response.content

    async def aclose(self) -> None:
        await self._client.aclose()
