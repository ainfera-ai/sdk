"""Ainfera quickstart — 60-second working example.

Run::

    pip install --no-cache-dir 'ainfera>=1.1.0'
    python examples/quickstart.py

What this does
==============

1. Mints a new Agent via the public ``agents.signup`` SDK method
   (no API key required for this call — it returns one).
2. Runs one signed Inference through the platform.
3. Prints the audit-chain URLs anyone can hit to verify the call
   independently.

The minted Agent is yours to keep. Save the ``api_key`` printed in
step 1 — it is shown once and never re-served.

SDK 1.1.0 (AIN-79) end-to-end
=============================

Prior to 1.1.0 this quickstart fell back to ``httpx`` because the
SDK shipped against pre-D4 mocks. From 1.1.0 the ``AinferaClient``
agents resource (``signup`` / ``register`` / ``retrieve``) and the
inference flow round-trip cleanly against the production /v1/* API.

Re-running this script is safe — each call mints a new Agent with a
fresh timestamped handle, so you can iterate without state cleanup.
"""

from __future__ import annotations

import os
import sys
import time

from ainfera import AinferaClient
from ainfera import __version__ as sdk_version

API_BASE = os.environ.get("AINFERA_API_BASE", "https://api.ainfera.ai")


def main() -> int:
    print(f"  ainfera SDK     = {sdk_version}")
    print(f"  API base        = {API_BASE}")
    print()

    # ── Step 1: anonymous signup ────────────────────────────────────
    # The signup endpoint is public — it provisions a Tenant + Agent +
    # Wallet bundle and returns a one-time api_key. We then construct a
    # bound client with that api_key for steps 2+.
    print("→ Minting Agent Card…")
    handle = f"quickstart-{int(time.time())}"
    owner = os.environ.get("GITHUB_USER", "anonymous")
    owner_source = "github_user" if owner != "anonymous" else "anonymous"

    bootstrap = AinferaClient(api_key="", base_url=API_BASE)
    try:
        result = bootstrap.agents.signup(
            agent_handle=handle,
            owner_handle=owner,
            owner_source=owner_source,
        )
    except Exception as exc:  # pragma: no cover — illustrative
        print(f"  ✗ Signup failed: {exc}", file=sys.stderr)
        return 1

    print(f"  ✓ agent_id      = {result.agent_id}")
    print(f"  ✓ did:web       = {result.did_web}")
    print(f"  ✓ canonical     = {result.canonical_uri}")
    print(f"  ⚠ api_key       = {result.api_key[:20]}…   (shown once — save it)")

    # ── Step 2: signed inference ────────────────────────────────────
    # Re-construct the client with the freshly-minted api_key, fetch the
    # Agent the SDK way, and call .inference(...).
    client = AinferaClient(api_key=result.api_key, base_url=API_BASE)
    agent = client.agents.retrieve(result.agent_id)

    print("\n→ Running first signed Inference…")
    try:
        inference = agent.inference(
            model="ainfera-inference",
            messages=[
                {
                    "role": "user",
                    "content": "Reply with exactly: 'soft launch alive'",
                }
            ],
            max_tokens=20,
        )
    except Exception as exc:  # pragma: no cover — illustrative
        print(f"  ✗ Inference failed: {exc}", file=sys.stderr)
        return 1

    print(f"  ✓ content       = {inference.content!r}")
    print(f"  ✓ model_used    = {inference.model_used}")
    print(f"  ✓ tokens        = {inference.input_tokens} in / {inference.output_tokens} out")
    print(f"  ✓ cost_usd      = ${inference.cost_usd}")
    print(f"  ✓ inference_id  = {inference.inference_id}")
    print(f"  ✓ receipt_id    = {inference.receipt_id}")
    print(f"  ✓ finish_reason = {inference.finish_reason}")

    # ── Step 3: audit trail ─────────────────────────────────────────
    print("\n→ Audit trail (no auth required):")
    print(f"  Public feed   : {API_BASE}/v1/audit/public")
    print(f"  This agent    : {API_BASE}/v1/audit/{result.agent_id}")
    print(f"  Verify call   : {API_BASE}/v1/audit/{result.agent_id}/verify")
    print(f"  Annex IV      : {API_BASE}/v1/audit/{result.agent_id}/annex-iv")

    print("\n✅ Quickstart verified — your first signed Inference is on chain.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
