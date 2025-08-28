import os

import pytest


def pytest_runtest_setup(item):
    if "requires_service" in item.keywords and not os.getenv("ENABLE_SERVICE_TESTS"):
        pytest.skip("Skipping service-backed tests. Set ENABLE_SERVICE_TESTS=1 to run.")
