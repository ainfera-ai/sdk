"""Read an Agent's AuditChain."""

from ainfera import AinferaClient

client = AinferaClient(api_key="ainfera_...")
agent = client.agents.retrieve("ag_...")
for event in agent.audit_chain.events(limit=10):
    print(event.seq, event.event_type, event.created_at)
