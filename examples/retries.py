"""Retry with exponential backoff for production resilience.

The SDK does not auto-retry. Wrap calls in your own retry logic.
Semantic exceptions (WalletInsufficient, SpendPolicyExceeded, ModelUnavailable)
are not transient and should not be retried.
"""

import time

from ainfera import (
    AinferaClient,
    APIError,
    ModelUnavailable,
    SpendPolicyExceeded,
    WalletInsufficient,
)


def inference_with_retry(
    agent,
    *,
    model: str,
    messages: list,
    max_retries: int = 3,
    base_delay: float = 1.0,
    **kwargs,
):
    """Retry on transient 5xx errors with exponential backoff.

    Re-raises semantic exceptions immediately (they are not transient):
      - WalletInsufficient (402): top up the wallet
      - SpendPolicyExceeded (403): adjust the agent's caps
      - ModelUnavailable (422): pick a different model

    Retries only on 5xx APIError (server-side transient failures).
    """
    for attempt in range(max_retries):
        try:
            return agent.inference(model=model, messages=messages, **kwargs)
        except (WalletInsufficient, SpendPolicyExceeded, ModelUnavailable):
            raise  # not transient — caller must fix
        except APIError as exc:
            if exc.status_code >= 500 and attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                print(
                    f"  retry {attempt + 1}/{max_retries} after {delay}s (HTTP {exc.status_code})"
                )
                time.sleep(delay)
                continue
            raise
    raise RuntimeError("unreachable")  # loop always returns or raises


# ── Usage ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    client = AinferaClient(api_key="ainfera_...")
    agent = client.agents.retrieve("agent_...")

    response = inference_with_retry(
        agent,
        model="ainfera-inference",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=20,
    )
    print(response.content)
    client.close()
