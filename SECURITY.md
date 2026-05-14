# Security Policy

The `ainfera` SDK handles signing keys, JWS-signed AgentCards, wallet
balances, and tamper-evident audit chains. We take vulnerabilities in
this surface seriously.

## Reporting a vulnerability

**Do not open a public GitHub issue for security reports.**

Email **security@ainfera.ai** with:

- A description of the vulnerability and its impact
- Steps to reproduce (a proof-of-concept is appreciated)
- The SDK version (`python -c "import ainfera; print(ainfera.__version__)"`)
  and your Python version
- Any suggested remediation, if you have one

You will receive an acknowledgement within **2 business days**. We aim to
provide an assessment and remediation timeline within **5 business days**.

## Disclosure process

- We follow a **90-day coordinated disclosure** window. We will work with
  you on a timeline and credit you in the release notes unless you prefer
  to remain anonymous.
- Fixes ship in a patch release; the advisory is published once a fixed
  version is available on PyPI.

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | ✅        |

Pre-1.0, only the latest minor receives security patches.

## Scope

In scope:

- Signature verification bypasses (JWS / AgentCard)
- Hash-chain verification bypasses (`verify_chain`, `AuditChain.verify`)
- Credential or token leakage (API keys in logs, errors, or telemetry)
- TLS or transport-layer weaknesses introduced by the SDK

Out of scope:

- Vulnerabilities in the Ainfera API itself — report those via the same
  address; we will route them internally
- Issues requiring a compromised local environment (e.g. a malicious
  `AINFERA_API_KEY` already set by an attacker)
- Denial of service against your own account
