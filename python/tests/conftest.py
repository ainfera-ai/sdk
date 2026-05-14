"""Shared pytest fixtures.

The ``mock_api`` fixture mounts a respx router against the default
Ainfera base URL so individual tests can stub specific endpoints
without hitting the network.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
import respx
from ainfera import AinferaClient, AsyncAinferaClient

BASE_URL = "https://api.ainfera.ai"


@pytest.fixture
def mock_api() -> Iterator[respx.MockRouter]:
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        yield router


@pytest.fixture
def client(mock_api: respx.MockRouter) -> Iterator[AinferaClient]:
    c = AinferaClient(api_key="ak_test")
    try:
        yield c
    finally:
        c.close()


@pytest.fixture
async def aclient(mock_api: respx.MockRouter) -> AsyncAinferaClient:
    return AsyncAinferaClient(api_key="ak_test")
