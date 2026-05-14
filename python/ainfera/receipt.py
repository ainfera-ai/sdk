"""Receipt — per-Inference settlement receipt.

Maps to Ontology v1.0 §2 Receipt. Returned alongside every Inference and
links to the AuditChain entry for that call.
"""

from __future__ import annotations

from pydantic import BaseModel


class Receipt(BaseModel):
    """Per-Inference settlement receipt."""

    receipt_id: str
    inference_id: str
    audit_url: str
    cost_usd: float
