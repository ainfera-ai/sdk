"""Mint a JWS-signed AgentCard."""

from ainfera import AinferaClient

client = AinferaClient(api_key="ainfera_...")
agent = client.agents.register(name="my-agent")
card = agent.get_card()
print(card.kid)
print(card.payload)
