"""Inference — a single model call routed through Ainfera.

Maps to Ontology v1.0 §2 Inference. ``InferenceResponse`` carries the
provider's output text plus the Receipt that links the call into the
AuditChain.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from ainfera.receipt import Receipt


class Inference(BaseModel):
    """A single inference call routed through Ainfera."""

    inference_id: str
    agent_id: str
    model: str
    messages: list[dict[str, Any]]


class InferenceResponse(BaseModel):
    """The response returned by :meth:`Agent.inference`."""

    text: str
    inference: Inference
    receipt: Receipt
    raw: dict[str, Any] | None = None
