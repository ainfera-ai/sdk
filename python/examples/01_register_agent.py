"""Register an Agent."""

from ainfera import AinferaClient

client = AinferaClient(api_key="ainfera_...")
agent = client.agents.register(tenant_id="ten_...", name="my-agent")
print(agent.agent_id)
