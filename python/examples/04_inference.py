"""Make an Inference call routed through Ainfera."""

from ainfera import AinferaClient

client = AinferaClient(api_key="ak_...")
agent = client.agents.retrieve("ag_...")
response = agent.inference(
    model="ainfera-inference",  # the flagship route — Ainfera picks the best model
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.content)
print(response.receipt_id)  # links to this call's AuditChain entry
