"""The Home Connect integration."""

import asyncio
import logging
import voluptuous as vol
from requests import HTTPError
from homeassistant.config_entries import ConfigEntry  # pylint: disable=import-error, no-name-in-module
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET  # pylint: disable=import-error, no-name-in-module
from homeassistant.core import HomeAssistant  # pylint: disable=import-error, no-name-in-module
from homeassistant.helpers import aiohttp_client, config_entry_oauth2_flow, config_validation as cv  # pylint: disable=import-error, no-name-in-module
from .api import ConfigEntryAuth
from .config_flow import OAuth2FlowHandler
from .const import DOMAIN
from .device import Washer, Dryer, Dishwasher, Freezer, FridgeFreezer, Oven, CoffeeMaker, Hood, Hob, WasherDryer, Refrigerator, WineCooler

OAUTH2_AUTHORIZE = "https://api.home-connect.com/security/oauth/authorize"
OAUTH2_TOKEN = "https://api.home-connect.com/security/oauth/token"

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({vol.Required(CONF_CLIENT_ID): cv.string, vol.Required(CONF_CLIENT_SECRET): cv.string})}, extra=vol.ALLOW_EXTRA)

PLATFORMS = ["binary_sensor", "sensor", "switch", "light"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Old way to set up integrations."""

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Home Connect from a config entry."""

    hass.data[DOMAIN] = {}

    client_id = entry.data.get(CONF_CLIENT_ID)
    client_secret = entry.data.get(CONF_CLIENT_SECRET)
    OAuth2FlowHandler.async_register_implementation(hass, config_entry_oauth2_flow.LocalOAuth2Implementation(hass, DOMAIN, client_id, client_secret, OAUTH2_AUTHORIZE, OAUTH2_TOKEN))

    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(hass, entry)

    # session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    # hass.data[DOMAIN][entry.entry_id] = ConfigEntryAuth(hass, entry, session)

    hass.data[DOMAIN][entry.entry_id] = ConfigEntryAuth(hass, entry, implementation)

    # Get the Home Connect interface
    home_connect = hass.data[DOMAIN][entry.entry_id]

    # Get a list of all Home Connect appliances like washer, dryer, oven.
    appliances = await hass.async_add_executor_job(home_connect.get_appliances)

    # Get a list of Home Connect devices and it's entities
    devices = []
    for appliance in appliances:
        if appliance.type == "Washer":
            device = Washer(hass, appliance)
            _LOGGER.debug("Washer detected")
        elif appliance.type == "Dryer":
            device = Dryer(hass, appliance)
            _LOGGER.debug("Dryer detected")
        elif appliance.type == "WasherDryer":
            device = WasherDryer(hass, appliance)
            _LOGGER.debug("Washer Dryer detected")
        elif appliance.type == "Refrigerator":
            device = Refrigerator(hass, appliance)
            _LOGGER.debug("Refrigerator detected")
        elif appliance.type == "WineCooler":
            device = WineCooler(hass, appliance)
            _LOGGER.debug("Wine Cooler detected")
        elif appliance.type == "Freezer":
            device = Freezer(hass, appliance)
            _LOGGER.debug("Freezer detected")
        elif appliance.type == "Dishwasher":
            device = Dishwasher(hass, appliance)
            _LOGGER.debug("Dishwasher detected")
        elif appliance.type == "FridgeFreezer":
            device = FridgeFreezer(hass, appliance)
            _LOGGER.debug("Fridge Freezer detected")
        elif appliance.type == "Oven":
            device = Oven(hass, appliance)
            _LOGGER.debug("Oven detected")
        elif appliance.type == "CoffeeMaker":
            device = CoffeeMaker(hass, appliance)
            _LOGGER.debug("Coffee Maker detected")
        elif appliance.type == "Hood":
            device = Hood(hass, appliance)
            _LOGGER.debug("Hood detected")
        elif appliance.type == "Hob":
            device = Hob(hass, appliance)
            _LOGGER.debug("Hob detected")
        else:
            _LOGGER.warning("Appliance type %s not implemented", appliance.type)
            continue

        # Initialize Home Connect device
        await hass.async_add_executor_job(device.initialize)

        # Put the device into the list of devices
        devices.append(device)

    # Save all found devices in home connect object
    home_connect.devices = devices

    for component in PLATFORMS:
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, component))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""

    unload_ok = all(await asyncio.gather(*[hass.config_entries.async_forward_entry_unload(entry, component) for component in PLATFORMS]))

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
