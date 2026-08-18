"""Integration tests configuration - allows network connections"""
import pytest
import pytest_socket


@pytest.hookimpl(trylast=True)
def pytest_runtest_setup():
    """Allow integration tests to use real network connections.

    Uses trylast=True to ensure this hook runs after pytest-homeassistant.
    pytest-homeassistant does two things: disable_socket() swaps out
    socket.socket, and socket_allow_hosts(["127.0.0.1"]) additionally
    intercepts socket.connect. Calling enable_socket() alone only undoes
    the former; connections are still blocked by the host allowlist,
    so _remove_restrictions() must also be called to restore connect.
    """
    pytest_socket.enable_socket()
    pytest_socket._remove_restrictions()


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
