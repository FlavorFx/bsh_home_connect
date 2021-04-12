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
        self.switches.append({"device": self, "key": "BSH.Common.Start", "description": "Start"})


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
        self.switches.append({"device": self, "key": "BSH.Common.Start", "description": "Start"})


class WasherDryer(Appliance):
    """Washer Dryer."""

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
                {"device": self, "key": "LaundryCare.Dryer.Option.DryingTarget", "description": "Drying Target", "unit": None, "icon": "mdi:water-percent", "device_class": "home_connect_drying_target"},
            ]
        )
        self.switches.append({"device": self, "key": "BSH.Common.Start", "description": "Start"})


class Dishwasher(Appliance):
    """Dishwasher."""

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
                {"device": self, "key": "BSH.Common.Root.SelectedProgram", "description": "Program", "unit": None, "icon": "mdi:format-list-bulleted", "device_class": "home_connect_dishcare_program"},
            ]
        )
        self.switches.append({"device": self, "key": "BSH.Common.Start", "description": "Start"})
        self.lights.append({"device": self, "key": "BSH.Common.Setting.AmbientLightEnabled", "description": "Ambient Light"})


class Refrigerator(Appliance):
    """Refrigerator."""

    def __init__(self, hass, appliance):
        super().__init__(hass, appliance)
        self.binary_sensors.extend(
            [
                {"device": self, "key": "BSH.Common.Status.DoorState", "description": "Door", "device_class": "door"},
            ]
        )
        self.sensors.extend(
            [
                {"device": self, "key": "Refrigeration.Common.Setting.BottleCooler.SetpointTemperature", "description": "Bottle Coller Temperature", "unit": TEMP_CELSIUS, "icon": "mdi:coolant-temperature", "device_class": None},
                {"device": self, "key": "Refrigeration.Common.Setting.ChillerLeft.SetpointTemperature", "description": "Chiller Left Temperature", "unit": TEMP_CELSIUS, "icon": "mdi:coolant-temperature", "device_class": None},
                {"device": self, "key": "Refrigeration.Common.Setting.ChillerCommon.SetpointTemperature", "description": "Chiller Temperature", "unit": TEMP_CELSIUS, "icon": "mdi:coolant-temperature", "device_class": None},
                {"device": self, "key": "Refrigeration.Common.Setting.ChillerRight.SetpointTemperature", "description": "Chiller Right Temperature", "unit": TEMP_CELSIUS, "icon": "mdi:coolant-temperature", "device_class": None},
                {"device": self, "key": "Refrigeration.FridgeFreezer.Setting.SetpointTemperatureRefrigerator", "description": "Temperature", "unit": TEMP_CELSIUS, "icon": "mdi:coolant-temperature", "device_class": None},
            ]
        )
        self.switches.extend(
            [
                {"device": self, "key": "Refrigeration.FridgeFreezer.Setting.SuperModeRefrigerator", "description": "Super Mode Refrigerator"},
                {"device": self, "key": "Refrigeration.Common.Setting.EcoMode", "description": "Eco Mode"},
                {"device": self, "key": "Refrigeration.Common.Setting.SabbathMode", "description": "Sabbath Mode"},
                {"device": self, "key": "Refrigeration.Common.Setting.VacationMode", "description": "Vacation Mode"},
                {"device": self, "key": "Refrigeration.Common.Setting.FreshMode", "description": "Fresh Mode"},
            ]
        )


class WineCooler(Appliance):
    """Wine Cooler."""

    def __init__(self, hass, appliance):
        super().__init__(hass, appliance)
        self.binary_sensors.extend(
            [
                {"device": self, "key": "BSH.Common.Status.DoorState", "description": "Door", "device_class": "door"},
            ]
        )
        self.sensors.extend(
            [
                {"device": self, "key": "Refrigeration.Common.Setting.WineCompartment.SetpointTemperature", "description": "Temperature 1", "unit": TEMP_CELSIUS, "icon": "mdi:coolant-temperature", "device_class": None},
                {"device": self, "key": "Refrigeration.Common.Setting.WineCompartment2.SetpointTemperature", "description": "Temperature 2", "unit": TEMP_CELSIUS, "icon": "mdi:coolant-temperature", "device_class": None},
                {"device": self, "key": "Refrigeration.Common.Setting.WineCompartment3.SetpointTemperature", "description": "Temperature 3", "unit": TEMP_CELSIUS, "icon": "mdi:coolant-temperature", "device_class": None},
            ]
        )
        self.switches.append({"device": self, "key": "Refrigeration.Common.Setting.SabbathMode", "description": "Sabbath Mode"})


class Freezer(Appliance):
    """Freezer."""

    def __init__(self, hass, appliance):
        super().__init__(hass, appliance)
        self.binary_sensors.extend(
            [
                {"device": self, "key": "BSH.Common.Status.DoorState", "description": "Door", "device_class": "door"},
            ]
        )
        self.sensors.extend(
            [
                {"device": self, "key": "Refrigeration.FridgeFreezer.Setting.SetpointTemperatureFreezer", "description": "Temperature", "unit": TEMP_CELSIUS, "icon": "mdi:coolant-temperature", "device_class": None},
            ]
        )
        self.switches.extend(
            [
                {"device": self, "key": "Refrigeration.FridgeFreezer.Setting.SuperModeFreezer", "description": "Super Mode Freezer"},
                {"device": self, "key": "Refrigeration.Common.Setting.EcoMode", "description": "Eco Mode"},
                {"device": self, "key": "Refrigeration.Common.Setting.SabbathMode", "description": "Sabbath Mode"},
            ]
        )


class FridgeFreezer(Appliance):
    """FridgeFreezer."""

    def __init__(self, hass, appliance):
        super().__init__(hass, appliance)
        self.binary_sensors.extend(
            [
                {"device": self, "key": "BSH.Common.Status.DoorState", "description": "Door", "device_class": "door"},
            ]
        )
        self.sensors.extend(
            [
                {"device": self, "key": "Refrigeration.FridgeFreezer.Setting.SetpointTemperatureFreezer", "description": "Freezer Temperature", "unit": TEMP_CELSIUS, "icon": "mdi:coolant-temperature", "device_class": None},
                {"device": self, "key": "Refrigeration.FridgeFreezer.Setting.SetpointTemperatureRefrigerator", "description": "Refrigerator Temperature", "unit": TEMP_CELSIUS, "icon": "mdi:coolant-temperature", "device_class": None},
                {"device": self, "key": "Refrigeration.Common.Setting.BottleCooler.SetpointTemperature", "description": "Bottle Temperature", "unit": TEMP_CELSIUS, "icon": "mdi:coolant-temperature", "device_class": None},
                {"device": self, "key": "Refrigeration.Common.Setting.ChillerLeft.SetpointTemperature", "description": "Chiller Left Temperature", "unit": TEMP_CELSIUS, "icon": "mdi:coolant-temperature", "device_class": None},
                {"device": self, "key": "Refrigeration.Common.Setting.ChillerCommon.SetpointTemperature", "description": "Chiller Temperature", "unit": TEMP_CELSIUS, "icon": "mdi:coolant-temperature", "device_class": None},
                {"device": self, "key": "Refrigeration.Common.Setting.ChillerRight.SetpointTemperature", "description": "Chiller Right Temperature", "unit": TEMP_CELSIUS, "icon": "mdi:coolant-temperature", "device_class": None},
            ]
        )
        self.switches.extend(
            [
                {"device": self, "key": "Refrigeration.FridgeFreezer.Setting.SuperModeRefrigerator", "description": "Super Mode Refrigerator"},
                {"device": self, "key": "Refrigeration.FridgeFreezer.Setting.SuperModeFreezer", "description": "Super Mode Freezer"},
                {"device": self, "key": "Refrigeration.Common.Setting.EcoMode", "description": "Eco Mode"},
                {"device": self, "key": "Refrigeration.Common.Setting.SabbathMode", "description": "Sabbath Mode"},
                {"device": self, "key": "Refrigeration.Common.Setting.VacationMode", "description": "Vacation Mode"},
                {"device": self, "key": "Refrigeration.Common.Setting.FreshMode", "description": "Fresh Mode"},
            ]
        )


class Oven(Appliance):
    """Oven."""

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
                {"device": self, "key": "BSH.Common.Option.Duration", "description": "Duration", "unit": TIME_SECONDS, "icon": "mdi:update", "device_class": None},
                {"device": self, "key": "BSH.Common.Option.ElapsedProgramTime", "description": "ElapsedProgramTime", "unit": TIME_SECONDS, "icon": "mdi:update", "device_class": None},
                {"device": self, "key": "BSH.Common.Option.ProgramProgress", "description": "Progress", "unit": PERCENTAGE, "icon": "mdi:progress-clock", "device_class": None},
                {"device": self, "key": "BSH.Common.Root.SelectedProgram", "description": "Program", "unit": None, "icon": "mdi:format-list-bulleted", "device_class": "home_connect_oven_program"},
                {"device": self, "key": "Cooking.Oven.Status.CurrentCavityTemperature", "description": "Current Cavity Temperature", "unit": TEMP_CELSIUS, "icon": "mdi:coolant-temperature", "device_class": None},
                {"device": self, "key": "Cooking.Oven.Option.SetpointTemperature", "description": "Temperature", "unit": TEMP_CELSIUS, "icon": "mdi:coolant-temperature", "device_class": None},
            ]
        )
        self.switches.append({"device": self, "key": "BSH.Common.Start", "description": "Start"})


class CoffeeMaker(Appliance):
    """Coffee Maker."""

    def __init__(self, hass, appliance):
        super().__init__(hass, appliance)
        self.binary_sensors.extend(
            [
                {"device": self, "key": "BSH.Common.Status.RemoteControlStartAllowed", "description": "Remote Control", "device_class": None},
            ]
        )
        self.sensors.extend(
            [
                {"device": self, "key": "BSH.Common.Status.OperationState", "description": "Operation State", "unit": None, "icon": None, "device_class": "home_connect_operation"},
            ]
        )
        self.switches.append({"device": self, "key": "BSH.Common.Start", "description": "Start"})


class Hood(Appliance):
    """Hood. / Dunstabzugshaube"""

    def __init__(self, hass, appliance):
        super().__init__(hass, appliance)
        self.binary_sensors.extend(
            [
                {"device": self, "key": "BSH.Common.Status.RemoteControlStartAllowed", "description": "Remote Control", "device_class": None},
            ]
        )
        self.switches.append({"device": self, "key": "BSH.Common.Start", "description": "Start"})
        self.lights.extend(
            [
                {"device": self, "key": "Cooking.Common.Setting.Lighting", "description": "Light"},
                {"device": self, "key": "BSH.Common.Setting.AmbientLightEnabled", "description": "Ambient Light"},
            ]
        )


class Hob(Appliance):
    """Hob. / Herd"""

    def __init__(self, hass, appliance):
        super().__init__(hass, appliance)
        self.sensors.extend(
            [
                {"device": self, "key": "BSH.Common.Status.OperationState", "description": "Operation State", "unit": None, "icon": None, "device_class": "home_connect_operation"},
            ]
        )


class WarmingDrawer(Appliance):
    """WarmingDrawer."""

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
            ]
        )
        self.switches.append({"device": self, "key": "BSH.Common.Start", "description": "Start"})
