"""Make an Inference call routed through Ainfera."""

from ainfera import AinferaClient

client = AinferaClient(api_key="ainfera_...")
agent = client.agents.retrieve("ag_...")
response = agent.inference(
    model="claude-opus-4-7",
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.text)
print(response.receipt.audit_url)
