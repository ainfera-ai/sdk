"""Ainfera — the Inference of AI Agents.

Signed AgentCards, x402-ready Wallets, hash-chained AuditChains — out of
the box. See https://ainfera.ai/docs/sdk-python for the full reference.
"""

from ainfera._version import __version__
from ainfera.agent_card import AgentCard
from ainfera.agents import Agent, AsyncAgent
from ainfera.audit import AsyncAuditChain, AuditChain, AuditEvent
from ainfera.client import AinferaClient, AsyncAinferaClient
from ainfera.exceptions import (
    AgentCardInvalid,
    AinferaError,
    APIError,
    AuditChainBroken,
    ModelUnavailable,
    SpendPolicyExceeded,
    WalletInsufficient,
)
from ainfera.inference import Inference, InferenceResponse
from ainfera.ledger import AsyncLedger, Ledger, LedgerEntry
from ainfera.receipt import Receipt
from ainfera.verify import verify_chain, verify_event_hash
from ainfera.wallet import AsyncWallet, Wallet

__all__ = [
    "__version__",
    # Clients
    "AinferaClient",
    "AsyncAinferaClient",
    # Agent
    "Agent",
    "AsyncAgent",
    "AgentCard",
    # Inference
    "Inference",
    "InferenceResponse",
    # Wallet / Ledger
    "Wallet",
    "AsyncWallet",
    "Ledger",
    "AsyncLedger",
    "LedgerEntry",
    # Audit
    "AuditEvent",
    "AuditChain",
    "AsyncAuditChain",
    # Receipt
    "Receipt",
    # Local verification primitives
    "verify_chain",
    "verify_event_hash",
    # Exceptions
    "AinferaError",
    "APIError",
    "AgentCardInvalid",
    "ModelUnavailable",
    "WalletInsufficient",
    "SpendPolicyExceeded",
    "AuditChainBroken",
]
