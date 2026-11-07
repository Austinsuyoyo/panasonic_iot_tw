"""Integration tests configuration - allows network connections"""
import socket

import pytest
import pytest_socket

# Captured at import time, before pytest-homeassistant's per-test setup
# replaces them with resolvers that refuse every non-local host name.
_REAL_RESOLVERS = (socket.getaddrinfo, socket.gethostbyname, socket.gethostbyname_ex)


@pytest.hookimpl(trylast=True)
def pytest_runtest_setup():
    """Allow integration tests to use real network connections.

    Uses trylast=True to ensure this hook runs after pytest-homeassistant.
    pytest-homeassistant does three things: disable_socket() swaps out
    socket.socket, socket_allow_hosts(["127.0.0.1"]) additionally
    intercepts socket.connect, and the socket module's resolvers raise
    "DNS resolution disabled in tests". Calling enable_socket() alone only
    undoes the first; _remove_restrictions() restores connect, and the
    saved resolvers restore DNS.
    """
    if _REAL_RESOLVERS[0].__module__ != "socket":
        # Fail only these tests, not the whole session's collection
        pytest.fail("socket resolvers were already patched when this conftest was imported; cannot restore DNS")
    pytest_socket.enable_socket()
    pytest_socket._remove_restrictions()
    socket.getaddrinfo, socket.gethostbyname, socket.gethostbyname_ex = _REAL_RESOLVERS


@pytest.fixture(autouse=True)
def expected_lingering_timers() -> bool:
    """Real API calls use TLS; aiohttp's SSL close timer fires after the test ends."""
    return True


@pytest.fixture(autouse=True)
def expected_lingering_tasks() -> bool:
    """Same as above: connection close cleanup doesn't count as a test leak."""
    return True


@pytest.fixture(autouse=True)
def verify_cleanup():
    """Disable the HA test framework's resource cleanup check.

    These tests make real TLS connections, and aiohttp leaves its own
    close threads and timers behind. In unit tests that would indicate
    a leak, but here it's just connection teardown and shouldn't fail
    the test.
    """
    yield
