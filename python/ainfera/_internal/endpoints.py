"""API endpoint paths.

Centralized so the inevitable reconciliation against the canonical API
Contract is a single-file diff. All paths are relative to the configured
``base_url`` (default ``https://api.ainfera.ai``).

SDK 1.1.0 (AIN-79): paths realigned to the production `/v1/*` surface.
Previous 1.0.x paths were written against pre-D4 mocks and did not
round-trip against prod — see CHANGELOG for the full migration list.
"""

from __future__ import annotations

API_VERSION = "v1"


# Agents collection + signup
def agents_collection() -> str:
    return f"/{API_VERSION}/agents"


def agent_register() -> str:
    return f"/{API_VERSION}/agents/register"


def agent_signup() -> str:
    return f"/{API_VERSION}/agents/signup"


def agent(agent_id: str) -> str:
    return f"/{API_VERSION}/agents/{agent_id}"


def agent_card(agent_id: str) -> str:
    return f"/{API_VERSION}/agents/{agent_id}/card"


# Inference — note flat /v1/inference, agent_id travels in request body.
def inference() -> str:
    return f"/{API_VERSION}/inference"


# Wallets — flat /v1/wallets/{agent_id}, topup body carries agent_id.
def wallet(agent_id: str) -> str:
    return f"/{API_VERSION}/wallets/{agent_id}"


def wallet_topup() -> str:
    return f"/{API_VERSION}/wallets/topup"


# Ledger — flat /v1/ledger/{agent_id}.
def ledger(agent_id: str) -> str:
    return f"/{API_VERSION}/ledger/{agent_id}"


# Audit — flat /v1/audit/{agent_id}, with /verify + /annex-iv subpaths.
def audit_chain(agent_id: str) -> str:
    return f"/{API_VERSION}/audit/{agent_id}"


def audit_verify(agent_id: str) -> str:
    return f"/{API_VERSION}/audit/{agent_id}/verify"


def audit_annex_iv(agent_id: str) -> str:
    return f"/{API_VERSION}/audit/{agent_id}/annex-iv"


# Receipts
def receipt(receipt_id: str) -> str:
    return f"/{API_VERSION}/receipts/{receipt_id}"
