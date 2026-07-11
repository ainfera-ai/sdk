"""Production error handling — semantic exception hierarchy.

The SDK maps HTTP status codes to semantic exception types so callers can
handle specific failure modes without parsing error messages.
"""

from ainfera import (
    AinferaClient,
    AinferaError,
    APIError,
    ModelUnavailable,
    SpendPolicyExceeded,
    WalletInsufficient,
)


def safe_inference(agent, model: str, messages: list) -> str:
    """Run inference with production-grade error handling.

    Returns the response content on success, or a user-facing error message.
    """
    try:
        response = agent.inference(model=model, messages=messages)
        return response.content
    except WalletInsufficient as exc:
        # 402 — wallet balance below request cost
        return f"Payment required: top up the agent wallet. ({exc})"
    except SpendPolicyExceeded as exc:
        # 403 — agent's spend policy blocked this call
        return f"Spend policy exceeded: adjust caps or use a cheaper model. ({exc})"
    except ModelUnavailable as exc:
        # 422 — requested model not available from any provider
        return f"Model '{exc.model}' unavailable. Try ainfera-inference for routing. ({exc})"
    except APIError as exc:
        # Other 4xx/5xx
        return f"API error (HTTP {exc.status_code}): {exc}"
    except AinferaError as exc:
        # SDK-level errors (e.g. not bound to a client)
        return f"SDK error: {exc}"


# ── Usage ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    client = AinferaClient(api_key="ainfera_...")
    agent = client.agents.retrieve("agent_...")

    result = safe_inference(
        agent,
        model="ainfera-inference",
        messages=[{"role": "user", "content": "Hello"}],
    )
    print(result)
    client.close()
