"""Config flow for Google Sheets integration."""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any

from google.oauth2.credentials import Credentials
from gspread.client import Client
from gspread.exceptions import GSpreadException
from homeassistant.config_entries import (
    SOURCE_REAUTH,
    ConfigEntry,
    ConfigFlowResult,
)
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from homeassistant.core import callback
from homeassistant.helpers import config_entry_oauth2_flow

from .const import DEFAULT_ACCESS, DEFAULT_NAME, DOMAIN
from .options import GoogleSheetsOptionsFlowHandler

if TYPE_CHECKING:
    from collections.abc import Mapping

_LOGGER = logging.getLogger(__name__)


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Google Sheets OAuth2 authentication."""

    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data that needs to be appended to the authorize url."""
        return {
            "scope": DEFAULT_ACCESS,
            # Add params to ensure we get back a refresh token
            "access_type": "offline",
            "prompt": "consent",
        }

    async def async_step_reauth(self, _: Mapping[str, Any]) -> ConfigFlowResult:
        """Perform reauth upon an API authentication error."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauth dialog."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")
        return await self.async_step_user()

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create an entry for the flow, or update existing entry."""
        service = Client(
            Credentials(data[CONF_TOKEN][CONF_ACCESS_TOKEN])  # type: ignore[no-untyped-call]
        )

        if self.source == SOURCE_REAUTH:
            reauth_entry = self._get_reauth_entry()
            try:
                await self.hass.async_add_executor_job(service.list_spreadsheet_files)
            except GSpreadException:
                _LOGGER.exception(
                    "Could not access spreadsheet files with the new token for entry %s:",  # noqa: E501
                    reauth_entry.unique_id,
                )
                return self.async_abort(reason="open_spreadsheet_failure")

            return self.async_update_reload_and_abort(reauth_entry, data=data)

        try:
            await self.hass.async_add_executor_job(service.list_spreadsheet_files)
        except GSpreadException:
            _LOGGER.exception(
                "Error accessing spreadsheet files with the new token",
            )
            return self.async_abort(reason="create_spreadsheet_failure")

        await self.async_set_unique_id(str(uuid.uuid4()))
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=DEFAULT_NAME, data=data)

    @staticmethod
    @callback
    def async_get_options_flow(
        _: ConfigEntry,
    ) -> GoogleSheetsOptionsFlowHandler:
        """Return the options flow handler for Google Sheets integration."""
        return GoogleSheetsOptionsFlowHandler()
