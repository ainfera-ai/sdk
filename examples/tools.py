"""Tool use through Ainfera inference."""

from ainfera import AinferaClient

client = AinferaClient(api_key="ak_...")
agent = client.agents.retrieve("ag_...")

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                },
                "required": ["location"],
            },
        },
    }
]

response = agent.inference(
    model="ainfera-inference",
    messages=[{"role": "user", "content": "What is the weather in Jakarta?"}],
    tools=tools,
)

print(response.text)
if response.tool_calls:
    for call in response.tool_calls:
        print(f"Tool: {call.function.name}({call.function.arguments})")
