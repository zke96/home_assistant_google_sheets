"""Constants for google_sheets_utils."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "google_sheets_utils"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"

DEFAULT_NAME = "Google Sheets"
DEFAULT_ACCESS = "https://www.googleapis.com/auth/drive"
