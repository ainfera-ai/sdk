"""Async usage of the Ainfera SDK."""

import asyncio

from ainfera import AsyncAinferaClient


async def main() -> None:
    client = AsyncAinferaClient(api_key="ak_...")
    agent = await client.agents.retrieve("ag_...")

    response = await agent.inference(
        model="ainfera-inference",
        messages=[{"role": "user", "content": "Hello"}],
    )
    print(response.text)

    # Concurrent requests
    tasks = [
        agent.inference(
            model="ainfera-inference",
            messages=[{"role": "user", "content": f"Fact {i}"}],
        )
        for i in range(3)
    ]
    results = await asyncio.gather(*tasks)
    for r in results:
        print(r.text)


asyncio.run(main())
