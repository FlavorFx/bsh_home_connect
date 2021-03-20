"""Entity Base Sensor for Home Connect"""

import logging
from homeassistant.core import callback  # pylint: disable=import-error, no-name-in-module
from homeassistant.helpers.dispatcher import async_dispatcher_connect  # pylint: disable=import-error, no-name-in-module
from homeassistant.helpers.entity import Entity  # pylint: disable=import-error, no-name-in-module
from .const import DOMAIN, SIGNAL_UPDATE_ENTITIES

_LOGGER = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
class HomeConnectEntity(Entity):
    """Generic Home Connect entity base class."""

    def __init__(self, device, description) -> None:
        """Initialize the entity."""
        self._device = device
        self._description = description
        self._name = f"{self._device.appliance.name} {self._description}"

    @property
    def name(self):
        """Return the name of the sensor."""

        return self._name

    @property
    def unique_id(self):
        """Return the unique id base on the id returned by Home Connect and the entity name."""

        return f"{self._device.appliance.haId}-{self._description}"

    @property
    def available(self):
        """Return true if the sensor is available."""

        return self._device.appliance.is_connected

    @property
    def should_poll(self):
        """No polling needed."""

        return False

    @property
    def device_info(self):
        """Return info about the device."""

        return {"identifiers": {(DOMAIN, self._device.appliance.haId)}, "name": self._device.appliance.name, "manufacturer": self._device.appliance.brand, "model": self._device.appliance.vib}

    async def async_added_to_hass(self):
        """Register callbacks."""

        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_UPDATE_ENTITIES, self._update_callback))

    @callback
    def _update_callback(self, ha_id):
        """Update data."""

        if ha_id == self._device.appliance.haId:
            self.async_schedule_update_ha_state(True)

    @callback
    def async_entity_update(self):
        """Update the entity."""

        _LOGGER.debug("Entity update triggered on %s", self)

        self.async_schedule_update_ha_state(True)