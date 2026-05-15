# `ainfera-agent.yaml` — agent manifest

Drop one of these in each agent's directory. `ainfera install`
discovers them recursively and registers each agent under your GitHub
handle so it appears at `app.ainfera.ai/<your-handle>`.

## Schema

```yaml
handle: varda                  # required · 3-40 chars · [a-z0-9-]
framework: nemoclaw+openclaw   # required · free-form identifier shown on the dashboard
persona: |                     # optional · system-prompt seed (max 8192 chars)
  You are Varda, AI Co-Founder of Ainfera Inc.
per_call_cap_usd: 1.50         # optional · drain-proof per-Inference cap (0.001 – 100)
daily_cap_usd: 20.00           # optional · drain-proof per-day cap (0.01 – 10000)
wallet_address: 0xABC...       # optional · Base smart wallet address (40 hex chars)
metadata:                      # optional · arbitrary key-value tags
  role: ai-co-founder
  public: true
  pairs_with: manwe
```

## Drain-proof badging

If either `per_call_cap_usd` or `daily_cap_usd` is set, the dashboard
shows the **Protected** badge on the agent. Caps without both fields
are valid; the platform applies whichever is present.

## Identity

`ainfera install` proves identity to the platform with your `gh auth token`.
Run `gh auth login` first if you haven't. The install endpoint compares
the token's `.login` field against your `--handle` (defaulting to whatever
`gh api user -q .login` returns) and rejects mismatches with HTTP 403.

## Examples

### Solo agent in its own repo

```
my-agent/
├─ ainfera-agent.yaml
└─ runner.py
```

```yaml
# ainfera-agent.yaml
handle: my-agent
framework: langgraph
per_call_cap_usd: 0.25
daily_cap_usd: 5.00
```

### Fleet under one repo

```
ainfera-os/
└─ agents/
   ├─ varda/ainfera-agent.yaml
   ├─ namo/ainfera-agent.yaml
   └─ ...
```

Run `ainfera install --dir agents/` and each manifest registers as a
distinct agent under the same owning GitHub handle.
