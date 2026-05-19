"""Inference — a single model call routed through Ainfera.

Maps to Ontology v1.0 §2 Inference. ``InferenceResponse`` is the flat
schema returned by ``POST /v1/inference`` in API 1.0+ (SDK 1.1.0 realigned
from the pre-D4 nested mock shape).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel


class InferenceResponse(BaseModel):
    """The flat response returned by :meth:`Agent.inference`.

    Mirrors the API ``InferenceResponse`` model verbatim. The 1.0.x SDK
    wrapped this in a nested ``{text, inference, receipt, raw}`` shape that
    drifted from production; 1.1.0 surfaces the real fields.
    """

    inference_id: str
    receipt_id: str
    content: str
    # AIN-177: structured block list when the provider returned blocks
    # (Anthropic structured, future streaming-block adapters). ``None`` when
    # the provider returned a plain string.
    content_blocks: list[dict[str, Any]] | None = None
    model_used: str
    # AIN-126: provider attribution at the synchronous response layer.
    provider: str | None = None
    # AIN-176: OpenAI-canonical finish reason ({stop, length, tool_calls,
    # content_filter, function_call}). Raw provider-native value preserved
    # in ``finish_reason_native`` for debugging.
    finish_reason: str
    finish_reason_native: str | None = None
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal

    @property
    def text(self) -> str:
        """Backward-compat alias for :attr:`content` (deprecated; use ``content``).

        Lets 1.0.x callers continue reading ``response.text`` while they
        migrate; will be removed in 2.0.
        """
        return self.content
