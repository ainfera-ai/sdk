"""Register an Agent."""

from ainfera import AinferaClient

client = AinferaClient(api_key="ak_...")
agent = client.agents.register(name="my-agent", description="My first Ainfera agent")
print(agent.agent_id)
