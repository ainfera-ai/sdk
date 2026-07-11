"""Verify an inference receipt locally."""

from ainfera import AinferaClient
from ainfera.verify import verify_receipt

client = AinferaClient(api_key="ak_...")
agent = client.agents.retrieve("ag_...")

response = agent.inference(
    model="ainfera-inference",
    messages=[{"role": "user", "content": "Hello"}],
)

# Verify the receipt locally — no API call needed
result = verify_receipt(response.receipt)

if result.valid:
    print("Receipt is valid")
    print(f"  Sequence: {result.sequence}")
    print(f"  Previous hash: {result.previous_hash}")
    print(f"  Signature: {result.signature[:16]}...")
else:
    print(f"Receipt INVALID: {result.error}")

# Local verification proves log integrity relative to the published signing key.
# It does not prevent tampering — it makes tamper-evidence verifiable.
