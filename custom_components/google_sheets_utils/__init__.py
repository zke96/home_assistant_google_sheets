"""Support for Google Sheets."""

from __future__ import annotations

from typing import TYPE_CHECKING

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_config_entry_implementation,
)
from homeassistant.loader import async_get_loaded_integration

from custom_components.google_sheets_utils.data import GoogleSheetsIntegrationData

from .const import DEFAULT_ACCESS, DOMAIN
from .coordinator import GoogleSheetsDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type GoogleSheetsConfigEntry = ConfigEntry[GoogleSheetsIntegrationData]

HTTP_CLIENT_ERROR_MIN = 400
HTTP_CLIENT_ERROR_MAX = 500


async def async_setup_entry(
    hass: HomeAssistant, entry: GoogleSheetsConfigEntry
) -> bool:
    """Set up Google Sheets from a config entry."""
    implementation = await async_get_config_entry_implementation(hass, entry)
    session = OAuth2Session(hass, entry, implementation)
    coordinator = GoogleSheetsDataUpdateCoordinator(hass, entry)

    try:
        await session.async_ensure_token_valid()
    except aiohttp.ClientResponseError as err:
        if HTTP_CLIENT_ERROR_MIN <= err.status < HTTP_CLIENT_ERROR_MAX:
            msg = "OAuth session is not valid, reauth required"
            raise ConfigEntryAuthFailed(msg) from err
        raise ConfigEntryNotReady from err
    except aiohttp.ClientError as err:
        raise ConfigEntryNotReady from err

    if not async_entry_has_scopes(hass, entry):
        msg = "Required scopes are not present, reauth required"
        raise ConfigEntryAuthFailed(msg)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = GoogleSheetsIntegrationData(
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
        session=session,
    )

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


def async_entry_has_scopes(
    _: HomeAssistant, config_entry: GoogleSheetsConfigEntry
) -> bool:
    """Verify that the config entry desired scope is present in the oauth token."""
    return DEFAULT_ACCESS in config_entry.data.get(CONF_TOKEN, {}).get(
        "scope", ""
    ).split(" ")


async def async_unload_entry(
    hass: HomeAssistant, config_entry: GoogleSheetsConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(config_entry, ["sensor"])


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
