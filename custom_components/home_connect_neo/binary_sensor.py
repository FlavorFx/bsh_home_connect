"""Binary Sensor for Home Connect"""

import logging
from homeassistant.components.binary_sensor import BinarySensorEntity  # pylint: disable=import-error, no-name-in-module
from .const import DOMAIN, SIGNAL_UPDATE_ENTITIES
from .entity import HomeConnectEntity

_LOGGER = logging.getLogger(__name__)


###############################################################################
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add binary sensor in HA."""

    home_connect = hass.data[DOMAIN][config_entry.entry_id]

    # put all binary sensors of appliances into a list and add it to HA
    entities = []
    for device in home_connect.devices:
        # get a list of all binary sensors
        binary_sensor_list = device.get_binary_sensors()
        for i in binary_sensor_list:
            # create a home connect binary sensor
            binary_sensor = HomeConnectBinarySensor(i["device"], i["key"], i["description"], i["device_class"])
            # add binary sensor to the list
            entities.append(binary_sensor)

    # add all entities to HA
    async_add_entities(entities, True)


# -----------------------------------------------------------------------------
class HomeConnectBinarySensor(HomeConnectEntity, BinarySensorEntity):
    """binary sensor for Home Connect."""

    def __init__(self, device, key, description, device_class) -> None:
        """Initialize the entity."""

        super().__init__(device, description)
        self._device_class = device_class
        self._key = key
        self._state = None

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""

        return bool(self._state)

    @property
    def device_class(self):
        """Return the class of this binary_sensor."""

        return self._device_class

    async def async_update(self):
        """Update the binary sensor's status."""

        # all messages of this appliance are stored in status
        status = self._device.appliance.status

        # check if a message has been received already
        if self._key not in status:
            self._state = None
        elif "value" not in status[self._key]:
            self._state = None
        else:
            # Is there a door message?
            if self._key == "BSH.Common.Status.DoorState" and status[self._key].get("value") == "BSH.Common.EnumType.DoorState.Closed":
                self._state = False
                self._icon = "mdi:door-closed"
            elif self._key == "BSH.Common.Status.DoorState" and status[self._key].get("value") == "BSH.Common.EnumType.DoorState.Locked":
                self._state = False
                self._icon = "mdi:door-closed-lock"
            elif self._key == "BSH.Common.Status.DoorState" and status[self._key].get("value") == "BSH.Common.EnumType.DoorState.Open":
                self._state = True
                self._icon = "mdi:door-open"
            # Is there a power message?
            elif self._key == "BSH.Common.Setting.PowerState" and status[self._key].get("value") == "BSH.Common.EnumType.PowerState.On":
                self._state = True
            elif self._key == "BSH.Common.Setting.PowerState" and status[self._key].get("value") == "BSH.Common.EnumType.PowerState.Standby":
                self._state = False
            elif self._key == "BSH.Common.Setting.PowerState" and status[self._key].get("value") == "BSH.Common.EnumType.PowerState.Off":
                self._state = False
            # Is there a remote control message?
            elif self._key == "BSH.Common.Status.RemoteControlStartAllowed":
                self._state = status[self._key].get("value")
            else:
                _LOGGER.warning("Unexpected value for key: %s", self._key)
            # _LOGGER.debug("Updated, new state: %s", self._state)
