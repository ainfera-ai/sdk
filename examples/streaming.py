"""Streaming inference through Ainfera."""

from ainfera import AinferaClient

client = AinferaClient(api_key="ak_...")
agent = client.agents.retrieve("ag_...")

stream = agent.inference_stream(
    model="ainfera-inference",
    messages=[{"role": "user", "content": "Explain quantum computing in 3 sentences."}],
)

for chunk in stream:
    print(chunk.text, end="", flush=True)
print()
