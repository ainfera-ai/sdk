"""Mint a JWS-signed AgentCard."""

from ainfera import AinferaClient

client = AinferaClient(api_key="ak_...")
agent = client.agents.register(tenant_id="tn_...", name="my-agent")
card = agent.get_card()
print(card.kid)
print(card.payload)
