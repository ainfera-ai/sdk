"""Ainfera quickstart — 60-second working example.

Run::

    pip install --no-cache-dir 'ainfera==1.0.1'
    python examples/quickstart.py

What this does
==============

1. Mints a new Agent via the public ``/v1/agents/signup`` endpoint
   (no API key required for this call — it returns one).
2. Runs one signed Inference through the platform.
3. Prints the audit-chain URLs anyone can hit to verify the call
   independently.

The minted Agent is yours to keep. Save the ``api_key`` printed in
step 1 — it is shown once and never re-served.

Note on the 1.0.x SDK
=====================

This quickstart uses ``httpx`` directly against the JSON API. The
``ainfera`` 1.0.x SDK ships the canonical types and a ``AinferaClient``
that authenticates correctly, but several resource shapes and endpoint
paths still differ from the production ``/v1/*`` contract — they were
written against pre-D4 mocks. Until the 1.1.0 alignment lands, going
direct keeps the example honest and unbroken.

Re-running this script is safe — each call mints a new Agent with a
fresh timestamped handle, so you can iterate without state cleanup.
"""

from __future__ import annotations

import os
import sys
import time

import httpx

from ainfera import __version__ as sdk_version

API_BASE = "https://api.ainfera.ai"


def main() -> int:
    print(f"  ainfera SDK     = {sdk_version} (canonical types + client)")
    print(f"  API base        = {API_BASE}")
    print()

    # ── Step 1: anonymous signup ────────────────────────────────────
    print("→ Minting Agent Card…")
    handle = f"quickstart-{int(time.time())}"
    owner = os.environ.get("GITHUB_USER", "anonymous")
    owner_source = "github_user" if owner != "anonymous" else "anonymous"

    try:
        resp = httpx.post(
            f"{API_BASE}/v1/agents/signup",
            json={
                "agent_handle": handle,
                "owner_handle": owner,
                "owner_source": owner_source,
            },
            timeout=20,
        )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        print(f"  ✗ Signup failed: {e}", file=sys.stderr)
        return 1

    bundle = resp.json()
    agent_id = bundle["agent_id"]
    api_key = bundle["api_key"]

    print(f"  ✓ agent_id      = {agent_id}")
    print(f"  ✓ did:web       = {bundle['did_web']}")
    print(f"  ✓ canonical     = {bundle['canonical_uri']}")
    print(f"  ⚠ api_key       = {api_key[:20]}…   (shown once — save it)")

    # ── Step 2: signed inference ────────────────────────────────────
    print("\n→ Running first signed Inference…")
    try:
        resp = httpx.post(
            f"{API_BASE}/v1/inference",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "agent_id": agent_id,
                "model": "claude-haiku-4-5",
                "messages": [
                    {
                        "role": "user",
                        "content": "Reply with exactly: 'soft launch alive'",
                    }
                ],
                "max_tokens": 20,
            },
            timeout=60,
        )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        body = resp.text if "resp" in locals() else ""
        print(f"  ✗ Inference failed: {e}", file=sys.stderr)
        if body:
            print(f"    response: {body[:200]}", file=sys.stderr)
        return 1

    inference = resp.json()
    print(f"  ✓ content       = {inference['content']!r}")
    print(f"  ✓ model_used    = {inference['model_used']}")
    print(f"  ✓ tokens        = {inference['input_tokens']} in / {inference['output_tokens']} out")
    print(f"  ✓ cost_usd      = ${inference['cost_usd']}")
    print(f"  ✓ inference_id  = {inference['inference_id']}")
    print(f"  ✓ receipt_id    = {inference['receipt_id']}")
    print(f"  ✓ finish_reason = {inference['finish_reason']}")

    # ── Step 3: audit trail ─────────────────────────────────────────
    print("\n→ Audit trail (no auth required):")
    print(f"  Public feed   : {API_BASE}/v1/audit/public")
    print(f"  This agent    : {API_BASE}/v1/audit/{agent_id}")
    print(f"  Verify call   : {API_BASE}/v1/audit/{agent_id}/verify")
    print(f"  Annex IV      : {API_BASE}/v1/audit/{agent_id}/annex-iv")

    print("\n✅ Soft launch verified — your first signed Inference is on chain.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
