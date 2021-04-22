"""The Home Connect integration."""

import asyncio
import logging
import voluptuous as vol
from typing import Optional
from requests import HTTPError
from homeassistant.config_entries import ConfigEntry  # pylint: disable=import-error, no-name-in-module
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, ATTR_DEVICE_ID  # pylint: disable=import-error, no-name-in-module
from homeassistant.core import HomeAssistant  # pylint: disable=import-error, no-name-in-module
from homeassistant.helpers import aiohttp_client, config_entry_oauth2_flow, config_validation as cv  # pylint: disable=import-error, no-name-in-module
from homeassistant.helpers import device_registry  # pylint: disable=import-error, no-name-in-module
from .api import ConfigEntryAuth
from .config_flow import OAuth2FlowHandler
from .const import DOMAIN, BASE_URL, ENDPOINT_AUTHORIZE, ENDPOINT_TOKEN
from .device import Appliance, Washer, Dryer, Dishwasher, Freezer, FridgeFreezer, Oven, CoffeeMaker, Hood, Hob, WasherDryer, Refrigerator, WineCooler

_LOGGER = logging.getLogger(__name__)

SERVICE_OPTION_SCHEMA = vol.Schema(
    {
        vol.Required("device_name"): cv.string,
        vol.Required("key"): cv.string,
        vol.Required("value"): cv.string,
    }
)

PLATFORMS = ["binary_sensor", "sensor", "switch", "light"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Old way to set up integrations."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Home Connect from a config entry."""

    hass.data[DOMAIN] = {}

    async def async_service_option(call):
        device_name = call.data["device_name"]
        key = call.data["key"]
        value = call.data["value"]

        _haId = None
        registry = await device_registry.async_get_registry(hass)
        for device in registry.devices.values():
            for identifier in device.identifiers:
                if identifier[0] == DOMAIN and device.name == device_name:
                    _haId = identifier[1]
                    break
            else:
                continue
            break

        _appliance = None
        if _haId is not None:
            for hc in hass.data[DOMAIN].values():
                for dev_dict in hc.devices:
                    if dev_dict.appliance.haId == _haId:
                        _appliance = dev_dict.appliance
                        break
                else:
                    continue
                break

        if _appliance is not None:
            await hass.async_add_executor_job(getattr(_appliance, "set_programs_active_options_with_key"), key, value)

    hass.services.async_register(DOMAIN, "change_options", async_service_option, schema=SERVICE_OPTION_SCHEMA)

    client_id = entry.data.get(CONF_CLIENT_ID)
    client_secret = entry.data.get(CONF_CLIENT_SECRET)
    authorize_url = f"{BASE_URL}{ENDPOINT_AUTHORIZE}"
    token_url = f"{BASE_URL}{ENDPOINT_TOKEN}"
    OAuth2FlowHandler.async_register_implementation(hass, config_entry_oauth2_flow.LocalOAuth2Implementation(hass, DOMAIN, client_id, client_secret, authorize_url, token_url))

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
            _LOGGER.info("Washer detected")
        elif appliance.type == "Dryer":
            device = Dryer(hass, appliance)
            _LOGGER.info("Dryer detected")
        elif appliance.type == "WasherDryer":
            device = WasherDryer(hass, appliance)
            _LOGGER.info("Washer Dryer detected")
        elif appliance.type == "Refrigerator":
            device = Refrigerator(hass, appliance)
            _LOGGER.info("Refrigerator detected")
        elif appliance.type == "WineCooler":
            device = WineCooler(hass, appliance)
            _LOGGER.info("Wine Cooler detected")
        elif appliance.type == "Freezer":
            device = Freezer(hass, appliance)
            _LOGGER.info("Freezer detected")
        elif appliance.type == "Dishwasher":
            device = Dishwasher(hass, appliance)
            _LOGGER.info("Dishwasher detected")
        elif appliance.type == "FridgeFreezer":
            device = FridgeFreezer(hass, appliance)
            _LOGGER.info("Fridge Freezer detected")
        elif appliance.type == "Oven":
            device = Oven(hass, appliance)
            _LOGGER.info("Oven detected")
        elif appliance.type == "CoffeeMaker":
            device = CoffeeMaker(hass, appliance)
            _LOGGER.info("Coffee Maker detected")
        elif appliance.type == "Hood":
            device = Hood(hass, appliance)
            _LOGGER.info("Hood detected")
        elif appliance.type == "Hob":
            device = Hob(hass, appliance)
            _LOGGER.info("Hob detected")
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
