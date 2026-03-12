"""Custom types for integration_blueprint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.config_entry_oauth2_flow import (
        OAuth2Session,
    )
    from homeassistant.loader import Integration

    from .coordinator import GoogleSheetsDataUpdateCoordinator


type GoogleSheetsConfigEntry = ConfigEntry[GoogleSheetsIntegrationData]


@dataclass
class GoogleSheetsIntegrationData:
    """Data for the Google Sheets integration."""

    coordinator: GoogleSheetsDataUpdateCoordinator
    integration: Integration
    session: OAuth2Session
