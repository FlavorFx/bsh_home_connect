"""Sensor for Home Connect"""

import logging
from homeassistant.helpers.entity import Entity  # pylint: disable=import-error, no-name-in-module
from .const import DOMAIN, SIGNAL_UPDATE_ENTITIES
from .entity import HomeConnectEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors in HA."""

    home_connect = hass.data[DOMAIN][config_entry.entry_id]

    # put all sensors of the appliances into a list and add it to HA
    entities = []
    for device in home_connect.devices:
        # get a list of all sensors
        sensor_list = device.get_sensors()
        for i in sensor_list:
            # create a home connect sensor
            sensor = HomeConnectSensor(i["device"], i["key"], i["description"], i["unit"], i["icon"], i["device_class"])
            # add sensor to the list
            entities.append(sensor)

    # add all entities to HA
    async_add_entities(entities, True)


class HomeConnectSensor(HomeConnectEntity, Entity):
    """Sensor class for Home Connect."""

    def __init__(self, device, key, description, unit, icon, device_class) -> None:
        """Initialize the entity."""
        super().__init__(device, description)
        self._unit = unit
        self._icon = icon
        self._device_class = device_class
        self._key = key
        self._state = None

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def device_class(self):
        """Return the device class."""
        return self._device_class

    async def async_update(self):
        """Update the sensos status."""

        # get all messages of this appliance stored in status
        status = self._device.appliance.status

        # check if a message has been received already
        if self._key not in status:
            self._state = None
        elif "value" not in status[self._key]:
            self._state = None
        else:
            if self._key in [
                "BSH.Common.Status.OperationState",
                "BSH.Common.Option.RemainingProgramTime",
                "BSH.Common.Option.ProgramProgress",
                "BSH.Common.Option.Duration",
                "BSH.Common.Option.ElapsedProgramTime",
                "BSH.Common.Root.SelectedProgram",
                "LaundryCare.Washer.Option.Temperature",
                "LaundryCare.Washer.Option.SpinSpeed",
                "LaundryCare.Dryer.Option.DryingTarget",
                "Cooking.Oven.Status.CurrentCavityTemperature",
                "Cooking.Oven.Option.SetpointTemperature",
                "Refrigeration.Common.Setting.BottleCooler.SetpointTemperature",
                "Refrigeration.Common.Setting.ChillerLeft.SetpointTemperature",
                "Refrigeration.Common.Setting.ChillerCommon.SetpointTemperature",
                "Refrigeration.Common.Setting.ChillerRight.SetpointTemperature",
                "Refrigeration.Common.Setting.WineCompartment.SetpointTemperature",
                "Refrigeration.Common.Setting.WineCompartment2.SetpointTemperature",
                "Refrigeration.Common.Setting.WineCompartment3.SetpointTemperature",
                "Refrigeration.FridgeFreezer.Setting.SetpointTemperatureRefrigerator",
                "Refrigeration.FridgeFreezer.Setting.SetpointTemperatureFreezer",
            ]:
                self._state = status[self._key].get("value")
            else:
                _LOGGER.warning("Unexpected value for key: %s", self._key)
            # _LOGGER.debug("Updated, new state: %s", self._state)
