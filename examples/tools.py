"""Tools (function calling) pass-through via the Ainfera SDK."""

from ainfera import AinferaClient

client = AinferaClient(api_key="ainfera_...")
agent = client.agents.retrieve("agent_...")

response = agent.inference(
    model="ainfera-inference",
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name"},
                    },
                    "required": ["city"],
                },
            },
        }
    ],
    tool_choice="auto",
)

# The response may contain tool_use blocks in content_blocks
# (Anthropic-shape: {"type": "tool_use", "name": ..., "input": ...})
print(f"finish_reason: {response.finish_reason}")
if response.content_blocks:
    for block in response.content_blocks:
        print(f"block: {block}")
else:
    print(f"content: {response.content}")
