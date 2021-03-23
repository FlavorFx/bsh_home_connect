"""Light Sensor for Home Connect"""

import logging
from homeassistant.components.light import LightEntity  # pylint: disable=import-error, no-name-in-module
from .const import DOMAIN, SIGNAL_UPDATE_ENTITIES
from .entity import HomeConnectEntity
from .homeconnect import HomeConnectError

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add switch sensor in HA."""

    home_connect = hass.data[DOMAIN][config_entry.entry_id]

    # put all lights of the appliances into a list and add it to HA
    entities = []
    for device in home_connect.devices:  # pylint: disable=unused-variable
        pass

    # add all entities to HA
    async_add_entities(entities, True)


class HomeConnectLight(HomeConnectEntity, LightEntity):
    """Light class for Home Connect."""

    def __init__(self, device, key, description) -> None:
        """Initialize the entity."""

        super().__init__(device, description)
