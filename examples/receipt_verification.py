"""Receipt verification — verify the audit trail for a specific call.

Every inference response carries a receipt_id linking to an AuditChain entry.
Receipts are returned inline on the response — there is no GET /v1/receipts/{id}
endpoint. To verify the integrity of the audit trail (which includes this
call's receipt), walk the AuditChain locally.
"""

from ainfera import AinferaClient, verify_chain

client = AinferaClient(api_key="ainfera_...")
agent = client.agents.retrieve("agent_...")

# 1. Run an inference — the response carries the receipt inline
response = agent.inference(
    model="ainfera-inference",
    messages=[{"role": "user", "content": "Hello"}],
)
print(f"inference_id: {response.inference_id}")
print(f"receipt_id:   {response.receipt_id}")
print(f"cost_usd:     ${response.cost_usd}")

# 2. Fetch all audit events and verify the hash chain locally
#    This proves log integrity relative to the published key — no Ainfera
#    trust required. An Annex IV auditor can run the same check offline.
events = list(agent.audit_chain.events())
print(f"audit events: {len(events)}")

try:
    assert verify_chain(events) is True
    print("chain intact: True")
except Exception as exc:
    print(f"chain broken: {exc}")

client.close()
