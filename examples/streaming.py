"""Streaming inference via the OpenAI-compatible endpoint.

SSE streaming is not available on POST /v1/inference (returns 501).
Use the OpenAI SDK pointed at api.ainfera.ai for streaming.

Install: pip install openai
"""

import os

from openai import OpenAI

client = OpenAI(
    base_url="https://api.ainfera.ai/v1",
    api_key=os.environ["AINFERA_API_KEY"],
)

stream = client.chat.completions.create(
    model="ainfera-inference",
    messages=[{"role": "user", "content": "Write a haiku about inference routing."}],
    stream=True,
)

for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)

print()  # newline after stream completes
