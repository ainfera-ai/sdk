"""API endpoint paths.

Centralized here so the inevitable reconciliation against the canonical
API Contract v1.0 is a single-file diff. All paths are relative to the
configured ``base_url`` (default ``https://api.ainfera.ai``).
"""

from __future__ import annotations

API_VERSION = "v1"


def agents_collection() -> str:
    return f"/{API_VERSION}/agents"


def agent(agent_id: str) -> str:
    return f"/{API_VERSION}/agents/{agent_id}"


def agent_card(agent_id: str) -> str:
    return f"/{API_VERSION}/agents/{agent_id}/card"


def agent_pubkey(agent_id: str) -> str:
    return f"/{API_VERSION}/agents/{agent_id}/pubkey"


def agent_wallet(agent_id: str) -> str:
    return f"/{API_VERSION}/agents/{agent_id}/wallet"


def agent_wallet_topup(agent_id: str) -> str:
    return f"/{API_VERSION}/agents/{agent_id}/wallet/topup"


def agent_wallet_ledger(agent_id: str) -> str:
    return f"/{API_VERSION}/agents/{agent_id}/wallet/ledger"


def agent_inference(agent_id: str) -> str:
    return f"/{API_VERSION}/agents/{agent_id}/inference"


def agent_audit(agent_id: str) -> str:
    return f"/{API_VERSION}/agents/{agent_id}/audit"


def receipt(receipt_id: str) -> str:
    return f"/{API_VERSION}/receipts/{receipt_id}"
