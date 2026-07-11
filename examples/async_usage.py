"""Async usage — AsyncAinferaClient for async/await callers."""

import asyncio

from ainfera import AsyncAinferaClient


async def main() -> None:
    client = AsyncAinferaClient(api_key="ainfera_...")
    try:
        agent = await client.agents.retrieve("agent_...")

        response = await agent.inference(
            model="ainfera-inference",
            messages=[{"role": "user", "content": "Hello"}],
        )
        print(f"content: {response.content}")
        print(f"model_used: {response.model_used}")
        print(f"cost: ${response.cost_usd}")

        # Wallet is awaitable on async agents
        wallet = await agent.wallet
        print(f"balance: ${wallet.balance_usd}")

        # Verify audit chain locally (offline, no trust required)
        ok = await agent.audit_chain.verify()
        print(f"chain intact: {ok}")
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
