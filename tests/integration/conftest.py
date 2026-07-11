"""Integration tests configuration - 允許網路連接"""
import pytest
from pytest_socket import enable_socket


@pytest.hookimpl(trylast=True)
def pytest_runtest_setup():
    """允許 integration 測試使用真實網路連接

    使用 trylast=True 確保這個 hook 在 pytest-homeassistant 之後執行，
    從而覆蓋其 socket 阻擋設置。

    enable_socket() 會完全移除 socket 限制，恢復原始的 socket.socket。
    """
    enable_socket()
