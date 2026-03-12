"""Options flow handler for configuring Google Sheets integration options in Home Assistant."""  # noqa: E501

import voluptuous as vol
from homeassistant.config_entries import ConfigFlowResult, OptionsFlow


class GoogleSheetsOptionsFlowHandler(OptionsFlow):
    """Options flow handler for configuring Google Sheets integration options."""

    async def async_step_init(self, user_input: dict | None = None) -> ConfigFlowResult:
        """
        Handle the initial step of the options flow for Google Sheets integration.

        Parameters
        ----------
        user_input : dict or None, optional
            The user input from the options form, by default None.

        Returns
        -------
        object
            The result of the options flow step, either showing the form or creating an entry.

        """  # noqa: E501
        cellscopy = self.config_entry.options.get("cells", []).copy()
        if user_input is not None:
            # Add the new cell config
            cellscopy.append(
                {
                    "spreadsheet_id": user_input["spreadsheet_id"],
                    "worksheet": user_input.get("worksheet", "Sheet1"),
                    "cell": user_input["cell"],
                }
            )
            return self.async_create_entry(title="", data={"cells": cellscopy})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("spreadsheet_id"): str,
                    vol.Required("worksheet", default="Sheet1"): str,
                    vol.Required("cell"): str,
                }
            ),
            description_placeholders={},
        )
