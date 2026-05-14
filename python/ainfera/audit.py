"""AuditChain — tamper-evident hash-chained record of Agent activity.

Maps to Ontology v1.0 §2 AuditEvent / AuditChain. Each AuditEvent's hash
covers the previous event's hash plus the canonical JSON of its own
payload, making the chain locally verifiable without trusting Ainfera.

``events()`` follows cursor-based pagination: the API returns a page of
events plus a ``next_cursor``, and the SDK walks pages until the cursor
runs out. This matters for :meth:`AuditChain.verify` — verifying only a
truncated prefix of the chain would be a silent correctness hole.
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
# caller's `limit` (a total cap); the SDK pages internally at this size.
_PAGE_SIZE = 100


class AuditEvent(BaseModel):
    """A single tamper-evident event in an Agent's AuditChain."""

    event_id: str
    agent_id: str
    seq: int
    event_type: str
    payload: dict[str, Any]
    previous_hash: str | None
    event_hash: str
    created_at: datetime


class AuditChain(BaseModel):
    """The append-only AuditChain for an Agent (sync flavor)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_id: str

    _http: HttpClient | None = PrivateAttr(default=None)

    def events(self, *, limit: int | None = None) -> Iterator[AuditEvent]:
        """Yield AuditEvents in sequence order (oldest first).

        Args:
            limit: Maximum number of events to yield. ``None`` (the
                default) walks the entire chain, following pagination
                cursors until exhausted.
        """
        http = self._require_http()
        yielded = 0
        cursor: str | None = None
        while limit is None or yielded < limit:
            params: dict[str, Any] = {"limit": _page_size(limit, yielded)}
            if cursor is not None:
                params["cursor"] = cursor
            body = http.request("GET", endpoints.agent_audit(self.agent_id), params=params)
            for raw in body.get("data", []):
                yield AuditEvent.model_validate(raw)
                yielded += 1
                if limit is not None and yielded >= limit:
                    return
            cursor = body.get("next_cursor")
            if not cursor:
                return

    def verify(self) -> bool:
        """Walk the full chain and verify the hash chain locally.

        Returns ``True`` if intact. Raises :class:`ainfera.AuditChainBroken`
        at the first broken link.
        """
        from ainfera.verify import verify_chain

        return verify_chain(list(self.events()))

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
        """Yield AuditEvents in sequence order (oldest first).

        Args:
            limit: Maximum number of events to yield. ``None`` (the
                default) walks the entire chain, following pagination
                cursors until exhausted.
        """
        http = self._require_http()
        yielded = 0
        cursor: str | None = None
        while limit is None or yielded < limit:
            params: dict[str, Any] = {"limit": _page_size(limit, yielded)}
            if cursor is not None:
                params["cursor"] = cursor
            body = await http.request(
                "GET", endpoints.agent_audit(self.agent_id), params=params
            )
            for raw in body.get("data", []):
                yield AuditEvent.model_validate(raw)
                yielded += 1
                if limit is not None and yielded >= limit:
                    return
            cursor = body.get("next_cursor")
            if not cursor:
                return

    async def verify(self) -> bool:
        """Walk the full chain and verify the hash chain locally."""
        from ainfera.verify import verify_chain

        events = [event async for event in self.events()]
        return verify_chain(events)

    def _require_http(self) -> AsyncHttpClient:
        if self._http is None:
            raise RuntimeError("AsyncAuditChain is not bound to a client")
        return self._http


def _page_size(limit: int | None, yielded: int) -> int:
    """Page size for the next request — never overshoot the caller's ``limit``."""
    if limit is None:
        return _PAGE_SIZE
    return min(_PAGE_SIZE, limit - yielded)
