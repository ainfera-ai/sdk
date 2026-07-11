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
    # Empty api_key is the documented "unauthenticated bootstrap" mode used
    # to call public endpoints like POST /v1/agents/signup. Omit the
    # Authorization header rather than send `Bearer ` with no value, which
    # some upstream proxies reject as malformed.
    headers: dict[str, str] = {
        "User-Agent": _user_agent(),
        "Accept": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _parse_body(response: httpx.Response) -> dict[str, Any]:
    try:
        body = response.json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


def _detail_message(body: dict[str, Any]) -> str | None:
    # FastAPI HTTPException(detail=...) shape: top-level `detail` may be a
    # string or a structured dict (e.g. /v1/inference 502 wraps upstream
    # provider failures as {"code": ..., "upstream_status": ..., "upstream_body": ...}).
    # Flatten the structured form so str(exception) is debuggable instead of
    # just "Bad Gateway".
    detail = body.get("detail")
    if isinstance(detail, str):
        return detail
    if isinstance(detail, dict):
        code = detail.get("code")
        upstream_status = detail.get("upstream_status")
        if code and upstream_status is not None:
            return f"{code} upstream_status={upstream_status}"
        if code:
            return str(code)
    return None


def _is_spend_policy_exceeded(body: dict[str, Any]) -> bool:
    """True only for gateway spend-cap refusals, not generic 403s."""
    code = body.get("code") or body.get("error")
    if code == "spend_policy_exceeded":
        return True
    detail = body.get("detail")
    if isinstance(detail, dict):
        dcode = detail.get("code") or detail.get("error")
        return dcode == "spend_policy_exceeded"
    return False


def _map_error(response: httpx.Response) -> APIError:
    body = _parse_body(response)
    message = (
        body.get("message")
        or body.get("error")
        or _detail_message(body)
        or response.reason_phrase
        or "API error"
    )
    status = response.status_code

    if status == 402:
        return WalletInsufficient(message, body=body)
    if status == 403:
        if _is_spend_policy_exceeded(body):
            return SpendPolicyExceeded(message, body=body)
        return APIError(message, status_code=status, body=body)
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
        response = self._client.request(method, path, json=json, params=params, timeout=timeout_arg)
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
