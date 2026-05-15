# CLAUDE.md — sdk

> Project memory. Read first every session.

## Vocabulary lock (Ontology v1.0)

Match entity names verbatim:
Tenant, Agent, AgentCard, Inference, Provider, Model, Wallet, Ledger,
LedgerEntry, AuditEvent, AuditChain, Settlement, Skill, Receipt,
TrustScore, Lens, Voter, Council.

**Banned**: Exchange, Platform (alone), User (for end-customer),
Spark/Hermes/Letta/Vox/Mythos (as agent codenames), Prime broker (externally).
(`hermes-agent` lowercase IS allowed — NousResearch framework.)

## Agent fleet (6)
- Manwe (private, founder brain, Sonnet 4.6 + hermes-agent)
- Varda (PUBLIC #1, GPT-5.5 + NemoClaw + OpenClaw)
- Yavanna (PUBLIC #2, multi-model Sonnet+Grok, Public Voice + Customer Relations)
- Namo (internal, research, D14+)
- Aule (internal, code, LangGraph)
- Tulkas (internal, red-team, D14+)

## Brand v1.3
- bg #070B14 / #0A0E1A / #0E1322
- text #E8EDF5 / #8A9AB8
- accent #4D95E8 / #2766BD
- IBM Plex Sans 500 -0.022em (display) / IBM Plex Mono (numerics)

## Commit format
<type>(<scope>): <subject>, blank line, body, blank line, then:
Co-Authored-By: Claude <noreply@anthropic.com>

## Privacy
Brand voice only in public strings. Git config: hizrian@ainfera.ai (never legal name).

## Canonical specs
- Ontology v1.0: https://github.com/ainfera-ai/specs/blob/main/ontology/spec.md

## Pre-commit checks
ruff + mypy --strict + pytest (Python repos)
prettier + tsc + vitest (web repo)
markdownlint (specs repo)
