# Ainfera SDK examples

Working code snippets you can copy-paste-run against the live platform.
None of these examples mock the API — they hit `https://api.ainfera.ai`
and emit real events to the public audit chain.

## `quickstart.py`

The 60-second first-Inference example. Mints an Agent Card, runs one
signed Inference through `ainfera-inference` (the flagship route),
prints the audit URLs you can verify.

```bash
pip install --no-cache-dir 'ainfera>=1.1.0'
python examples/quickstart.py
```

Output should end with `✅ Quickstart verified`. The minted Agent
appears on `https://api.ainfera.ai/v1/audit/public` within seconds.

Set `GITHUB_USER=<your-handle>` before running to make the canonical
URI map to your GitHub identity instead of `anonymous`.

## `python/examples/`

In-depth examples covering individual API surfaces:

- `01_register_agent.py` — Register an agent via `client.agents.register()`
- `02_mint_card.py` — Fetch and verify a JWS-signed AgentCard
- `03_topup_wallet.py` — Top up an agent's wallet
- `04_inference.py` — Basic inference call
- `05_read_audit.py` — Read the audit chain
- `06_verify_chain.py` — Local hash-chain verification (offline, no trust)

## Using streaming, tools, and retries

See the [README](../README.md) for production patterns on:

- SSE streaming (via OpenAI/Anthropic SDK pointed at `api.ainfera.ai`)
- Tools / function calling (`tools=`, `tool_choice=`)
- Retry with exponential backoff
- Async usage (`AsyncAinferaClient`)
- Receipt verification and local AuditChain verification
