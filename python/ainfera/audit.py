"""AuditChain — tamper-evident hash-chained record of Agent activity.

Maps to Ontology v1.0 §2 AuditEvent / AuditChain. Each AuditEvent's hash
covers the previous event's hash plus the canonical JSON of its own
payload, making the chain locally verifiable without trusting Ainfera.

SDK 1.1.0 (AIN-79) realigned to ``GET /v1/audit/{agent_id}`` which
returns ``{agent_id, events: [...]}`` and supports ``since_seq`` for
incremental walks. Pre-1.1.0 cursor-based pagination is replaced by
seq-based windowing.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, PrivateAttr

from ainfera._internal import endpoints

if TYPE_CHECKING:
    from ainfera._internal.http import AsyncHttpClient, HttpClient

# Per-request page size when walking the chain. Independent of the
# caller's ``limit`` (a total cap); the SDK pages internally at this size.
# API caps at 500 per request.
_PAGE_SIZE = 500


class AuditEvent(BaseModel):
    """A single tamper-evident event in an Agent's AuditChain.

    Field shape mirrors the API ``AuditEvent`` model. ``event_id`` and
    legacy ``previous_hash`` aliases are preserved for backward-compat
    with 1.0.x callers; the API now returns ``id`` and ``prev_hash`` so
    both names bind.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: str | None = None
    agent_id: str
    seq: int
    event_type: str
    payload: dict[str, Any]
    previous_hash: str | None = None
    event_hash: str
    created_at: datetime

    # legacy alias
    @property
    def event_id(self) -> str | None:
        return self.id


class AuditVerifyResult(BaseModel):
    """Server-side chain verification result, from ``/v1/audit/{id}/verify``."""

    agent_id: str
    event_count: int
    valid: bool
    failure_seq: int | None = None
    failure_reason: str | None = None


class AuditChain(BaseModel):
    """The append-only AuditChain for an Agent (sync flavor)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_id: str

    _http: HttpClient | None = PrivateAttr(default=None)

    def events(self, *, limit: int | None = None) -> Iterator[AuditEvent]:
        """Yield AuditEvents in sequence order (oldest first).

        Walks pages via ``since_seq`` until exhausted or ``limit`` reached.
        """
        http = self._require_http()
        yielded = 0
        since: int | None = None
        while limit is None or yielded < limit:
            params: dict[str, Any] = {"limit": _page_size(limit, yielded)}
            if since is not None:
                params["since_seq"] = since
            body = http.request("GET", endpoints.audit_chain(self.agent_id), params=params)
            events = body.get("events") or body.get("data") or []
            if not events:
                return
            for raw in events:
                event = AuditEvent.model_validate(raw)
                yield event
                yielded += 1
                since = event.seq
                if limit is not None and yielded >= limit:
                    return

    def verify(self) -> bool:
        """Walk the full chain and verify the hash chain locally.

        Returns ``True`` if intact. Raises :class:`ainfera.AuditChainBroken`
        at the first broken link.
        """
        from ainfera.verify import verify_chain

        return verify_chain(list(self.events()))

    def verify_remote(self) -> AuditVerifyResult:
        """Ask the API to verify the chain server-side (audit reconciliation).

        Useful for "did Ainfera tamper" checks — the local :meth:`verify`
        is the canonical trust-no-one check, but ``verify_remote`` confirms
        that the canonical control plane agrees with the chain state at
        the moment of the call.
        """
        body = self._require_http().request("GET", endpoints.audit_verify(self.agent_id))
        return AuditVerifyResult.model_validate(body)

    def annex_iv_bundle(self) -> dict[str, Any]:
        """Fetch the Annex IV-style audit export bundle.

        EU AI Act Annex IV format export. The shape is large + evolving;
        returned as a raw dict rather than a Pydantic model to avoid
        churn on every Annex IV schema revision.
        """
        return self._require_http().request("GET", endpoints.audit_annex_iv(self.agent_id))

    def _require_http(self) -> HttpClient:
        if self._http is None:
            raise RuntimeError("AuditChain is not bound to a client")
        return self._http


class AsyncAuditChain(BaseModel):
    """The append-only AuditChain for an Agent (async flavor)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_id: str

    _http: AsyncHttpClient | None = PrivateAttr(default=None)

    async def events(self, *, limit: int | None = None) -> AsyncIterator[AuditEvent]:
        """Yield AuditEvents in sequence order (oldest first)."""
        http = self._require_http()
        yielded = 0
        since: int | None = None
        while limit is None or yielded < limit:
            params: dict[str, Any] = {"limit": _page_size(limit, yielded)}
            if since is not None:
                params["since_seq"] = since
            body = await http.request("GET", endpoints.audit_chain(self.agent_id), params=params)
            events = body.get("events") or body.get("data") or []
            if not events:
                return
            for raw in events:
                event = AuditEvent.model_validate(raw)
                yield event
                yielded += 1
                since = event.seq
                if limit is not None and yielded >= limit:
                    return

    async def verify(self) -> bool:
        """Walk the full chain and verify the hash chain locally."""
        from ainfera.verify import verify_chain

        events = [event async for event in self.events()]
        return verify_chain(events)

    async def verify_remote(self) -> AuditVerifyResult:
        """Ask the API to verify the chain server-side."""
        body = await self._require_http().request(
            "GET", endpoints.audit_verify(self.agent_id)
        )
        return AuditVerifyResult.model_validate(body)

    async def annex_iv_bundle(self) -> dict[str, Any]:
        """Fetch the Annex IV-style audit export bundle."""
        return await self._require_http().request(
            "GET", endpoints.audit_annex_iv(self.agent_id)
        )

    def _require_http(self) -> AsyncHttpClient:
        if self._http is None:
            raise RuntimeError("AsyncAuditChain is not bound to a client")
        return self._http


def _page_size(limit: int | None, yielded: int) -> int:
    """Page size for the next request — never overshoot the caller's ``limit``."""
    if limit is None:
        return _PAGE_SIZE
    return min(_PAGE_SIZE, limit - yielded)
