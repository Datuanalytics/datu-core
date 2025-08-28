import os
import sys
import types

import pytest

if "mcp_use" not in sys.modules:
    shim = types.ModuleType("mcp_use")

    class _Dummy:
        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, _name):
            def _noop(*args, **kwargs):
                return None

            return _noop

    shim.MCPAgent = _Dummy
    shim.MCPClient = _Dummy

    sys.modules["mcp_use"] = shim


def pytest_runtest_setup(item):
    if "requires_service" in item.keywords and not os.getenv("ENABLE_SERVICE_TESTS"):
        pytest.skip("Skipping service-backed tests. Set ENABLE_SERVICE_TESTS=1 to run.")
