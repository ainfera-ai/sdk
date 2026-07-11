"""Production error handling with Ainfera SDK."""

import logging

from ainfera import (
    AinferaClient,
    AuthenticationError,
    RateLimitError,
    ServerError,
)
from ainfera import (
    TimeoutError as APITimeoutError,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = AinferaClient(api_key="ak_...", timeout=30.0)
agent = client.agents.retrieve("ag_...")

try:
    response = agent.inference(
        model="ainfera-inference",
        messages=[{"role": "user", "content": "Hello"}],
    )
    print(response.text)

except AuthenticationError:
    logger.error("Invalid API key — check your credentials")

except RateLimitError as e:
    logger.warning(f"Rate limited — retry after {e.retry_after}s")

except APITimeoutError:
    logger.error("Request timed out — try a simpler prompt or increase timeout")

except ServerError as e:
    logger.error(f"Server error {e.status_code}: {e.message}")

except Exception as e:
    logger.exception(f"Unexpected error: {e}")
