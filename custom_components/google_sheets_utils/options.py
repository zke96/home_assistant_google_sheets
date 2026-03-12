"""Options flow handler for configuring Google Sheets integration options in Home Assistant."""  # noqa: E501

import voluptuous as vol
from homeassistant.config_entries import ConfigFlowResult, OptionsFlow
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .const import DOMAIN


class GoogleSheetsOptionsFlowHandler(OptionsFlow):
    """Options flow handler for configuring Google Sheets integration options."""

    async def async_step_init(self, user_input: dict | None = None) -> ConfigFlowResult:
        """
        Handle the initial step of the options flow for Google Sheets integration.

        Args:
            user_input (dict | None): User input from the options form.

        Returns:
            ConfigFlowResult: Result of the options flow step.

        """

        def _remove(registry: er.EntityRegistry, cell: str) -> None:
            """Remove an entity from the registry."""
            entity_id = registry.async_get_entity_id("sensor", DOMAIN, cell)
            if entity_id:
                registry.async_remove(entity_id)

        cellscopy = self.config_entry.options.get("cells", []).copy()
        if user_input is not None:
            # Remove selected cell configs
            to_remove = user_input.get("remove", None)
            cellscopy = [c for c in cellscopy if c != to_remove]
            if to_remove:
                registry = er.async_get(self.hass)
                _remove(registry, to_remove)

            # Add new cell config if provided
            if user_input.get("spreadsheet_id") and user_input.get("cell"):
                cellscopy.append(
                    {
                        "spreadsheet_id": user_input["spreadsheet_id"],
                        "worksheet": user_input.get("worksheet", "Sheet1"),
                        "cell": user_input["cell"],
                    }
                )
            return self.async_create_entry(title="", data={"cells": cellscopy})

        # Build choices for removal
        remove_choices = [
            selector.SelectOptionDict(
                label=f"{c['spreadsheet_id']} {c['worksheet']} {c['cell']}",
                value=f"gsheets_{c['spreadsheet_id']}_{c['worksheet']}_{c['cell']}",
            )
            for i, c in enumerate(cellscopy)
        ]

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional("remove"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=remove_choices,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional("spreadsheet_id"): str,
                    vol.Optional("worksheet", default="Sheet1"): str,
                    vol.Optional("cell"): str,
                }
            ),
            description_placeholders={},
        )
