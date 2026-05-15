# Ainfera SDK examples

Working code snippets you can copy-paste-run against the live platform.
None of these examples mock the API — they hit `https://api.ainfera.ai`
and emit real events to the public audit chain.

## `quickstart.py`

The 60-second first-Inference example. Mints an Agent Card, runs one
signed Inference through `claude-haiku-4-5`, prints the audit URLs you
can verify.

```bash
pip install --no-cache-dir 'ainfera==1.0.1'
python examples/quickstart.py
```

Output should end with `✅ Soft launch verified`. The minted Agent
appears on `https://api.ainfera.ai/v1/audit/public` within seconds.

Set `GITHUB_USER=<your-handle>` before running to make the canonical
URI map to your GitHub identity instead of `anonymous`.

## Coming next (D6+)

- Multi-provider routing example
- LangChain wrapper example
- MCP server agent example
- hermes-agent drop-in example
- OpenClaw skill example
