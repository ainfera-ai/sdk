"""Locally verify the AuditChain hash chain (no Ainfera trust required)."""

from ainfera import AinferaClient

client = AinferaClient(api_key="ainfera_...")
agent = client.agents.retrieve("ag_...")
assert agent.audit_chain.verify() is True
print("Audit chain intact.")
