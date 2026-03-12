"""Sensor platform for Google Sheets integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant

    from .coordinator import GoogleSheetsDataUpdateCoordinator
    from .data import GoogleSheetsConfigEntry

_LOGGER = logging.getLogger(__name__)

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="google_sheets_cell",
        name="Google Sheets Cell",
        icon="mdi:format-quote-close",
    ),
)


async def async_setup_entry(
    _: HomeAssistant, entry: GoogleSheetsConfigEntry, async_add_entities: Callable
) -> None:
    """Set up the sensor platform."""
    # Make sure runtime_data and coordinator exist
    if not getattr(entry, "runtime_data", None):
        _LOGGER.warning("No runtime_data on config entry; sensor setup skipped")
        return

    coordinator: GoogleSheetsDataUpdateCoordinator = entry.runtime_data.coordinator

    # Get spreadsheet/cell configs from entry.options
    cell_configs = entry.options.get("cells", [])
    if not cell_configs:
        _LOGGER.warning("No spreadsheet/cell configs found in options")
        return

    entities = [GoogleSheetsCellSensor(coordinator, config) for config in cell_configs]
    async_add_entities(entities)
    _LOGGER.debug("Google Sheets sensor entities added: %s", entities)


class GoogleSheetsCellSensor(CoordinatorEntity, SensorEntity):
    """A sensor representing a Google Sheets cell value."""

    def __init__(
        self,
        coordinator: GoogleSheetsDataUpdateCoordinator,
        config: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.spreadsheet_id = config["spreadsheet_id"]
        self.worksheet = config["worksheet"]
        self.cell = config["cell"]
        self._attr_name = f"Google Sheets {self.spreadsheet_id} {self.cell}"
        self._attr_unique_id = (
            f"gsheets_{self.spreadsheet_id}_{self.worksheet}_{self.cell}"
        )
        self._attr_icon = "mdi:google-spreadsheet"

    @property
    def native_value(self) -> str:
        """Return the current cell value."""
        key = f"{self.spreadsheet_id}_{self.worksheet}_{self.cell}"
        value = self.coordinator.data.get(key) if self.coordinator.data else None
        if value:
            self._attr_name = f"Google Sheets: {value.spreadsheet_name}-{value.worksheet_name}-{value.cell}"  # noqa: E501
            return value.cell_value
        return "N/A"
