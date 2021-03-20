"""API for Home Connect bound to Home Assistant OAuth."""

import logging
from asyncio import run_coroutine_threadsafe
from aiohttp import ClientSession
from homeassistant import config_entries, core  # pylint: disable=import-error, no-name-in-module
from homeassistant.const import DEVICE_CLASS_TIMESTAMP, PERCENTAGE, TIME_SECONDS  # pylint: disable=import-error, no-name-in-module
from homeassistant.helpers import config_entry_oauth2_flow  # pylint: disable=import-error, no-name-in-module
from homeassistant.helpers.dispatcher import dispatcher_send  # pylint: disable=import-error, no-name-in-module
from .homeconnect import HomeConnectAPI, HomeConnectError

_LOGGER = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
class ConfigEntryAuth(HomeConnectAPI):
    """Provide Home Connect authentication tied to an OAuth2 based config entry."""

    def __init__(self, hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry, implementation: config_entry_oauth2_flow.AbstractOAuth2Implementation):
        """Initialize Home Connect Auth."""

        self.hass = hass
        self.config_entry = config_entry
        self.session = config_entry_oauth2_flow.OAuth2Session(hass, config_entry, implementation)
        super().__init__(self.session.token)
        self.devives = []

    # def refresh_tokens(self) -> str:
    #    """Refresh and return new Home Connect tokens using Home Assistant OAuth2 session."""

    #    run_coroutine_threadsafe(self.session.async_ensure_token_valid(), self.hass.loop).result()
    #    _LOGGER.info("Token refreshed")

    #    return self.session.token["access_token"]

    def refresh_tokens(self) -> dict:
        """Refresh and return new Home Connect tokens using Home Assistant OAuth2 session."""

        run_coroutine_threadsafe(self.session.async_ensure_token_valid(), self.hass.loop).result()
        _LOGGER.info("Token refreshed")

        return self.session.token
