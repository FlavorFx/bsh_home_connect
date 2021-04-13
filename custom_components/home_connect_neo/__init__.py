"""The Home Connect integration."""

import asyncio
import logging
import voluptuous as vol
from typing import Optional
from requests import HTTPError
from homeassistant.config_entries import ConfigEntry  # pylint: disable=import-error, no-name-in-module
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, ATTR_ENTITY_ID  # pylint: disable=import-error, no-name-in-module
from homeassistant.core import HomeAssistant  # pylint: disable=import-error, no-name-in-module
from homeassistant.helpers import aiohttp_client, config_entry_oauth2_flow, config_validation as cv  # pylint: disable=import-error, no-name-in-module
from .api import ConfigEntryAuth
from .config_flow import OAuth2FlowHandler
from .const import DOMAIN, BASE_URL, ENDPOINT_AUTHORIZE, ENDPOINT_TOKEN
from .device import Appliance, Washer, Dryer, Dishwasher, Freezer, FridgeFreezer, Oven, CoffeeMaker, Hood, Hob, WasherDryer, Refrigerator, WineCooler

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({vol.Required(CONF_CLIENT_ID): cv.string, vol.Required(CONF_CLIENT_SECRET): cv.string})}, extra=vol.ALLOW_EXTRA)

PLATFORMS = ["binary_sensor", "sensor", "switch", "light"]

SERVICE_SELECT = "select_program"
SERVICE_PAUSE = "pause_program"
SERVICE_RESUME = "resume_program"
SERVICE_OPTION_ACTIVE = "set_option_active"
SERVICE_OPTION_SELECTED = "set_option_selected"
SERVICE_SETTING = "change_setting"

SERVICE_SETTING_SCHEMA = vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_id, vol.Required("key"): str, vol.Required("value"): vol.Coerce(str)})
SERVICE_PROGRAM_SCHEMA = vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_id, vol.Required("program"): str})
SERVICE_COMMAND_SCHEMA = vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_id})


async def async_setup(hass: HomeAssistant, config: dict):
    """Old way to set up integrations."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Home Connect from a config entry."""

    def _get_appliance_by_entity_id(hass: HomeAssistant, entity_id: str) -> Optional[Appliance]:
        """Return a Home Connect appliance instance given an entity_id."""
        for hc in hass.data[DOMAIN].values():
            for dev_dict in hc.devices:
                device = dev_dict["device"]
                for entity in device.entities:
                    if entity.entity_id == entity_id:
                        return device.appliance
        _LOGGER.error("Appliance for %s not found.", entity_id)
        return None

    async def _async_service_program(call, method):
        """Generic callback for services taking a program."""
        program = call.data["program"]
        entity_id = call.data[ATTR_ENTITY_ID]
        appliance = _get_appliance_by_entity_id(hass, entity_id)
        if appliance is not None:
            await hass.async_add_executor_job(getattr(appliance, method), program)

    async def _async_service_command(call, command):
        """Generic callback for services executing a command."""
        entity_id = call.data[ATTR_ENTITY_ID]
        appliance = _get_appliance_by_entity_id(hass, entity_id)
        if appliance is not None:
            await hass.async_add_executor_job(appliance.execute_command, command)

    async def _async_service_key_value(call, method):
        """Generic callback for services taking a key and value."""
        key = call.data["key"]
        value = call.data["value"]
        entity_id = call.data[ATTR_ENTITY_ID]
        appliance = _get_appliance_by_entity_id(hass, entity_id)
        if appliance is not None:
            await hass.async_add_executor_job(getattr(appliance, method), key, value)

    async def async_service_option_active(call):
        """Service for setting an option for an active program."""
        await _async_service_key_value(call, "set_options_active_program")

    async def async_service_option_selected(call):
        """Service for setting an option for a selected program."""
        await _async_service_key_value(call, "set_options_selected_program")

    async def async_service_pause(call):
        """Service for pausing a program."""
        await _async_service_command(call, "BSH.Common.Command.PauseProgram")

    async def async_service_resume(call):
        """Service for resuming a paused program."""
        await _async_service_command(call, "BSH.Common.Command.ResumeProgram")

    async def async_service_select(call):
        """Service for selecting a program."""
        await _async_service_program(call, "select_program")

    async def async_service_setting(call):
        """Service for changing a setting."""
        await _async_service_key_value(call, "set_setting")

    hass.data[DOMAIN] = {}

    hass.services.async_register(DOMAIN, SERVICE_OPTION_ACTIVE, async_service_option_active, schema=SERVICE_SETTING_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_OPTION_SELECTED, async_service_option_selected, schema=SERVICE_SETTING_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SETTING, async_service_setting, schema=SERVICE_SETTING_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_PAUSE, async_service_pause, schema=SERVICE_COMMAND_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_RESUME, async_service_resume, schema=SERVICE_COMMAND_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SELECT, async_service_select, schema=SERVICE_PROGRAM_SCHEMA)

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
