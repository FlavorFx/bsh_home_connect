"""API for Home Connect bound to Home Assistant OAuth."""

import logging
from homeassistant.const import DEVICE_CLASS_TIMESTAMP, PERCENTAGE, TEMP_CELSIUS, TIME_SECONDS  # pylint: disable=import-error, no-name-in-module
from homeassistant.helpers.dispatcher import dispatcher_send  # pylint: disable=import-error, no-name-in-module
from .const import SIGNAL_UPDATE_ENTITIES
from .homeconnect import HomeConnectError

_LOGGER = logging.getLogger(__name__)


class Appliance:
    """Home Connect generic device."""

    def __init__(self, hass, appliance):
        """Constructor"""
        self.hass = hass
        self.appliance = appliance
        self.binary_sensors = []
        self.sensors = []
        self.switches = []
        self.lights = []
        self.binary_sensors.append({"device": self, "key": "BSH.Common.Setting.PowerState", "description": "Power", "device_class": "power"})

    def initialize(self):
        """Initialize appliance."""
        # update status of appliance like setting, prograam, temperature, spin speed, etc.
        self.appliance.update_properties()
        # listen to events sent from appliance
        self.appliance.listen_events(callback=self.event_callback)

    def event_callback(self, appliance):
        """Handle event."""
        _LOGGER.debug("Update triggered on %s", appliance.name)
        # Dump the entire status buffer
        for key in self.appliance.status:
            value = self.appliance.status[key]
            # remove uri due to better readability
            if "uri" in value:
                value["uri"] = "none"
            _LOGGER.debug("%s: %s", key, value)
        # forward the event to home assistant entities
        dispatcher_send(self.hass, SIGNAL_UPDATE_ENTITIES, appliance.haId)

    def get_binary_sensors(self):
        """Get a dictionary with info about all binary sensors."""
        return self.binary_sensors

    def get_sensors(self):
        """Get a dictionary with info about all sensors."""
        return self.sensors

    def get_switches(self):
        """Get a dictionary with info about all switches."""
        return self.switches

    def get_lights(self):
        """Get a dictionary with info about all lights sensors."""
        return self.lights



class Washer(Appliance):
    """Washer."""

    def __init__(self, hass, appliance):
        super().__init__(hass, appliance)
        self.binary_sensors.extend(
            [
                {"device": self, "key": "BSH.Common.Status.RemoteControlStartAllowed", "description": "Remote Control", "device_class": None},
                {"device": self, "key": "BSH.Common.Status.DoorState", "description": "Door", "device_class": "door"},
            ]
        )
        self.sensors.extend(
            [
                {"device": self, "key": "BSH.Common.Status.OperationState", "description": "Operation State", "unit": None, "icon": None, "device_class": "home_connect_operation"},
                {"device": self, "key": "BSH.Common.Option.RemainingProgramTime", "description": "Remaining Time", "unit": TIME_SECONDS, "icon": "mdi:update", "device_class": None},
                {"device": self, "key": "BSH.Common.Option.ProgramProgress", "description": "Progress", "unit": PERCENTAGE, "icon": "mdi:progress-clock", "device_class": None},
                {"device": self, "key": "BSH.Common.Root.SelectedProgram", "description": "Program", "unit": None, "icon": "mdi:format-list-bulleted", "device_class": "home_connect_washer_program"},
                {"device": self, "key": "LaundryCare.Washer.Option.Temperature", "description": "Temperature", "unit": None, "icon": "mdi:coolant-temperature", "device_class": "home_connect_washer_temperatur"},
                {"device": self, "key": "LaundryCare.Washer.Option.SpinSpeed", "description": "Spin Speed", "unit": None, "icon": "mdi:rotate-right", "device_class": "home_connect_washer_spin_speed"},
            ]
        )
        self.switches.append({"device": self, "description": "Start"})


class Dryer(Appliance):
    """Dryer."""

    def __init__(self, hass, appliance):
        super().__init__(hass, appliance)
        self.binary_sensors.extend(
            [
                {"device": self, "key": "BSH.Common.Status.RemoteControlStartAllowed", "description": "Remote Control", "device_class": None},
                {"device": self, "key": "BSH.Common.Status.DoorState", "description": "Door", "device_class": "door"},
            ]
        )
        self.sensors.extend(
            [
                {"device": self, "key": "BSH.Common.Status.OperationState", "description": "Operation State", "unit": None, "icon": None, "device_class": "home_connect_operation"},
                {"device": self, "key": "BSH.Common.Option.RemainingProgramTime", "description": "Remaining Time", "unit": TIME_SECONDS, "icon": "mdi:update", "device_class": None},
                {"device": self, "key": "BSH.Common.Option.ProgramProgress", "description": "Progress", "unit": PERCENTAGE, "icon": "mdi:progress-clock", "device_class": None},
                {"device": self, "key": "BSH.Common.Root.SelectedProgram", "description": "Program", "unit": None, "icon": "mdi:format-list-bulleted", "device_class": "home_connect_dryer_program"},
                {"device": self, "key": "LaundryCare.Dryer.Option.DryingTarget", "description": "Drying Target", "unit": None, "icon": "mdi:water-percent", "device_class": "home_connect_drying_target"},
            ]
        )
        self.switches.append({"device": self, "description": "Start"})


class WasherDryer(Appliance):
    """Washer Dryer."""

    def __init__(self, hass, appliance):
        super().__init__(hass, appliance)


class Dishwasher(Appliance):
    """Dishwasher."""

    def __init__(self, hass, appliance):
        super().__init__(hass, appliance)


class Refrigerator(Appliance):
    """Refrigerator."""

    def __init__(self, hass, appliance):
        super().__init__(hass, appliance)


class WineCooler(Appliance):
    """Wine Cooler."""

    def __init__(self, hass, appliance):
        super().__init__(hass, appliance)


class Freezer(Appliance):
    """Freezer."""

    def __init__(self, hass, appliance):
        super().__init__(hass, appliance)


class FridgeFreezer(Appliance):
    """FridgeFreezer."""

    def __init__(self, hass, appliance):
        super().__init__(hass, appliance)


class Oven(Appliance):
    """Oven."""

    def __init__(self, hass, appliance):
        super().__init__(hass, appliance)


class CoffeeMaker(Appliance):
    """Coffee Maker."""

    def __init__(self, hass, appliance):
        super().__init__(hass, appliance)


class Hood(Appliance):
    """Hood."""

    def __init__(self, hass, appliance):
        super().__init__(hass, appliance)


class Hob(Appliance):
    """Hob."""

    def __init__(self, hass, appliance):
        super().__init__(hass, appliance)
