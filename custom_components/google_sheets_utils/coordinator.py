"""DataUpdateCoordinator for integration_blueprint."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from gspread import Client, WorksheetNotFound
from gspread.exceptions import APIError
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import GoogleSheetsConfigEntry

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=5)


async def async_fetch_cell_value(
    hass: HomeAssistant,
    config_entry: GoogleSheetsConfigEntry,
    spreadsheet_id: str,
    worksheet_name: str,
    cell: str,
) -> str:
    """Fetch a cell value from Google Sheets in a thread-safe way."""

    def _fetch() -> str:
        client = Client(Credentials(config_entry.data[CONF_TOKEN][CONF_ACCESS_TOKEN]))  # type: ignore[no-untyped-call]
        sheet = client.open_by_key(spreadsheet_id)
        worksheet = sheet.worksheet(worksheet_name)
        rows = worksheet.get_values(cell)
        if not rows or not rows[0]:
            msg = f"No value found in cell {cell} of worksheet {worksheet_name}"
            raise HomeAssistantError(msg)
        return worksheet.get_values(cell)[0][0]

    try:
        return await hass.async_add_executor_job(_fetch)
    except RefreshError:
        config_entry.async_start_reauth(hass)
        raise
    except WorksheetNotFound as ex:
        msg = f"Worksheet '{worksheet_name}' not found in spreadsheet '{spreadsheet_id}': {ex}"  # noqa: E501
        raise HomeAssistantError(msg) from ex
    except APIError as ex:
        msg = f"Failed to retrieve data: {ex}"
        raise HomeAssistantError(msg) from ex


class GoogleSheetsDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch and update cell values from Google Sheets for Home Assistant integration."""  # noqa: E501

    def __init__(
        self, hass: HomeAssistant, config_entry: GoogleSheetsConfigEntry
    ) -> None:
        """
        Initialize the coordinator with Home Assistant instance and cell configurations.

        Args:
            hass: Home Assistant instance.
            config_entry: Google Sheets config entry.

        """
        self.config_entry = config_entry
        self.hass = hass
        self.cell_configs = config_entry.options.get("cells", [])
        super().__init__(
            hass,
            _LOGGER,
            name="google_sheets_cell",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        results = {}
        for config in self.cell_configs:
            spreadsheet_id = config["spreadsheet_id"]
            worksheet = config["worksheet"]
            cell = config["cell"]
            value = await async_fetch_cell_value(
                self.hass, self.config_entry, spreadsheet_id, worksheet, cell
            )
            results[f"{spreadsheet_id}_{worksheet}_{cell}"] = value
        return results
