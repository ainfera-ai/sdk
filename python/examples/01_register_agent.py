"""Register an Agent."""

from ainfera import AinferaClient

client = AinferaClient(api_key="ak_...")
agent = client.agents.register(tenant_id="tn_...", name="my-agent")
print(agent.agent_id)
