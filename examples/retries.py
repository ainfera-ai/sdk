"""Retry strategies for Ainfera inference."""

from ainfera import AinferaClient

client = AinferaClient(
    api_key="ak_...",
    max_retries=3,
    retry_delay=1.0,
    retry_backoff=2.0,
    retry_on_status=[429, 500, 502, 503],
)

agent = client.agents.retrieve("ag_...")

response = agent.inference(
    model="ainfera-inference",
    messages=[{"role": "user", "content": "Hello"}],
)

print(response.text)
