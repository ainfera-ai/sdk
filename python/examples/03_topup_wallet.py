"""Top up an Agent's Wallet (prepaid path)."""

from ainfera import AinferaClient

client = AinferaClient(api_key="ainfera_...")
agent = client.agents.retrieve("ag_...")
agent.wallet.topup(amount_usd=10)
print(agent.wallet.balance_usd)
