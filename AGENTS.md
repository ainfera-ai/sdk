# AGENTS.md — operating contract for sdk

Audience: the Ainfera fleet (Aulë and peers) and any agent operating this repo. Read before touching code.

## Identity
- **Core** — the official **Python SDK** (`ainfera`): signed Agent Cards, routed inference, audit chain. Published to PyPI as `ainfera`.
- Source of truth for names: the Naming law (`hizrianraz/obsidian/_ontology/Naming.md`, v1.3).

## Naming (law v1.3) — use these exactly
- Canonical wire model string: **`ainfera-inference`**. `ainfera-mithril` / `ainfera-auto` are **silent legacy aliases** — the SDK should accept them and document the canonical string.
- This SDK is the package external customers and the internal fleet both consume — keep public method/field names stable (they are contracts).

## §0 Premise verification (mandatory)
Open every change with an explicit PASS/FAIL probe (clean tree? correct remote? tests green?) **before** editing. A failed premise → halt and surface; never fix-forward.

## Definition of done — verified, not PR proof
```bash
cd python && uv run pytest        # client, resources, agent-card signing/verify
# end-to-end: signup → routed inference → audit verify against api.ainfera.ai/v1
```
Done = tests green **and** a signed Agent Card round-trips through routed inference + audit verify. PR opened ≠ shipped.

## Secrets — hard rules
- `.env` is gitignored; `.env.example` is the template. `AINFERA_API_KEY` (`ainfera_*`) comes from the environment only — never commit, never echo a value.

## License
Apache-2.0. © Ainfera Inc. 2026.
