"""Unit tests for the Panasonic IoT TW config and options flows."""
from unittest.mock import patch

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.panasonic_iot_tw.config_flow import ConfigFlow, InvalidAuth
from custom_components.panasonic_iot_tw.const import (
    CONF_PROXY,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
)

@pytest.fixture(autouse=True)
def _enable(enable_custom_integrations):
    """Enable the custom integration for flow tests."""
    yield


@pytest.fixture(autouse=True)
def _mock_setup_entry():
    """Avoid real network setup when a flow creates or reloads an entry."""
    with patch(
        "custom_components.panasonic_iot_tw.async_setup_entry",
        return_value=True,
    ):
        yield


def _existing_entry(hass, username="user@example.com"):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: username, CONF_PASSWORD: "secret"},
        options={CONF_PROXY: "", CONF_UPDATE_INTERVAL: 180},
        unique_id=username.lower(),
        version=2,
    )
    entry.add_to_hass(hass)
    return entry


def test_flow_version():
    """The config flow declares VERSION 2."""
    assert ConfigFlow.VERSION == 2


async def test_user_flow_success(hass):
    """A valid account creates an entry with split data/options."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    with patch(
        "custom_components.panasonic_iot_tw.config_flow.validate_input",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "User@Example.com",
                CONF_PASSWORD: "secret",
                CONF_PROXY: "http://proxy:8080",
                CONF_UPDATE_INTERVAL: 240,
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_USERNAME: "User@Example.com",
        CONF_PASSWORD: "secret",
    }
    assert result["options"] == {
        CONF_PROXY: "http://proxy:8080",
        CONF_UPDATE_INTERVAL: 240,
    }
    assert result["result"].unique_id == "user@example.com"


async def test_user_flow_duplicate_aborts(hass):
    """Configuring the same account twice aborts."""
    _existing_entry(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "User@Example.com",
            CONF_PASSWORD: "secret",
        },
    )

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow_opens_without_error(hass):
    """The options flow opens (no TypeError from missing constructor arg)."""
    entry = _existing_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"


async def test_options_flow_saves(hass):
    """Submitting the options flow stores the new options."""
    entry = _existing_entry(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_PROXY: "http://p:1", CONF_UPDATE_INTERVAL: 300},
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_PROXY: "http://p:1", CONF_UPDATE_INTERVAL: 300}


async def test_reauth_flow_success(hass):
    """Reauth updates the password and reloads the entry."""
    entry = _existing_entry(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with patch(
        "custom_components.panasonic_iot_tw.config_flow.validate_input",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: "new-secret"}
        )

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_PASSWORD] == "new-secret"
    assert entry.data[CONF_USERNAME] == "user@example.com"


async def test_reauth_flow_invalid_auth(hass):
    """Reauth surfaces an invalid_auth error and stays on the form."""
    entry = _existing_entry(hass)
    result = await entry.start_reauth_flow(hass)

    with patch(
        "custom_components.panasonic_iot_tw.config_flow.validate_input",
        side_effect=InvalidAuth,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: "wrong"}
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_reconfigure_flow_password_change(hass):
    """Reconfigure updates the password without touching the unique_id."""
    entry = _existing_entry(hass)

    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    with patch(
        "custom_components.panasonic_iot_tw.config_flow.validate_input",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "user@example.com",
                CONF_PASSWORD: "new-secret",
                CONF_PROXY: "http://p:1",
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_PASSWORD] == "new-secret"
    assert entry.data[CONF_USERNAME] == "user@example.com"
    assert entry.unique_id == "user@example.com"
    assert entry.options[CONF_PROXY] == "http://p:1"
    # Unrelated options are preserved.
    assert entry.options[CONF_UPDATE_INTERVAL] == 180


async def test_reconfigure_flow_username_change_updates_unique_id(hass):
    """Reconfigure with a new username re-points the entry unique_id."""
    entry = _existing_entry(hass)

    result = await entry.start_reconfigure_flow(hass)

    with patch(
        "custom_components.panasonic_iot_tw.config_flow.validate_input",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "New@Example.com",
                CONF_PASSWORD: "secret",
                CONF_PROXY: "",
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_USERNAME] == "New@Example.com"
    assert entry.unique_id == "new@example.com"


async def test_reconfigure_flow_username_collision_aborts(hass):
    """Reconfigure to a username owned by another entry aborts."""
    entry = _existing_entry(hass, username="user@example.com")
    _existing_entry(hass, username="other@example.com")

    result = await entry.start_reconfigure_flow(hass)

    with patch(
        "custom_components.panasonic_iot_tw.config_flow.validate_input",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "Other@Example.com",
                CONF_PASSWORD: "secret",
                CONF_PROXY: "",
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    # Original entry is untouched.
    assert entry.data[CONF_USERNAME] == "user@example.com"
    assert entry.unique_id == "user@example.com"
