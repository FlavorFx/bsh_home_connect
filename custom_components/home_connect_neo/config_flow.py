"""Config flow for Home Connect."""

import logging
import voluptuous as vol
from homeassistant import config_entries  # pylint: disable=import-error, no-name-in-module
from homeassistant.helpers import config_entry_oauth2_flow  # pylint: disable=import-error, no-name-in-module
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET  # pylint: disable=import-error, no-name-in-module
from .const import DOMAIN, NAME, BASE_URL, ENDPOINT_AUTHORIZE, ENDPOINT_TOKEN


class OAuth2FlowHandler(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Config flow to handle Home Connect OAuth2 authentication."""

    DOMAIN = DOMAIN
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    def __init__(self):
        """Initialize the config flow."""
        super().__init__()
        self.client_id = None
        self.client_secret = None

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""

        errors = {}

        # Only one instance should be allowed
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        # Has the user already entered something?
        if user_input is not None:
            # Check the input is not empty and client ID and client secret has 64 character
            if user_input[CONF_CLIENT_ID] is not None and len(user_input[CONF_CLIENT_ID]) == 64 and user_input[CONF_CLIENT_SECRET] is not None and len(user_input[CONF_CLIENT_SECRET]) == 64:
                # Register your own Config Flow Handler
                self.client_id = user_input[CONF_CLIENT_ID]
                self.client_secret = user_input[CONF_CLIENT_SECRET]
                authorize_url = f"{BASE_URL}{ENDPOINT_AUTHORIZE}"
                token_url = f"{BASE_URL}{ENDPOINT_TOKEN}"
                OAuth2FlowHandler.async_register_implementation(self.hass, config_entry_oauth2_flow.LocalOAuth2Implementation(self.hass, DOMAIN, self.client_id, self.client_secret, authorize_url, token_url))

                # Hand over control of the parent class
                return await self.async_step_pick_implementation()
            else:
                # otherwise show an error message
                errors["base"] = "auth"

            # Open the dialog for entering Client ID and Client Secret
            return self.async_show_form(step_id="user", data_schema=vol.Schema({vol.Required(CONF_CLIENT_ID): str, vol.Required(CONF_CLIENT_SECRET): str}), errors=errors)

        # Open the dialog for entering Client ID and Client Secret
        return self.async_show_form(step_id="user", data_schema=vol.Schema({vol.Required(CONF_CLIENT_ID): str, vol.Required(CONF_CLIENT_SECRET): str}), errors=errors)

    async def async_oauth_create_entry(self, user_input):
        """Create an entry for the flow."""

        user_input[CONF_CLIENT_ID] = self.client_id
        user_input[CONF_CLIENT_SECRET] = self.client_secret

        return self.async_create_entry(title=NAME, data=user_input)