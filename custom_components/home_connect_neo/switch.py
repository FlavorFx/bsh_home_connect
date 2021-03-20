"""Switch for Home Connect"""

import logging
from homeassistant.components.switch import SwitchEntity  # pylint: disable=import-error, no-name-in-module
from .const import DOMAIN, SIGNAL_UPDATE_ENTITIES
from .entity import HomeConnectEntity
from .homeconnect import HomeConnectError

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add switch sensor in HA."""

    home_connect = hass.data[DOMAIN][config_entry.entry_id]

    # put all switches of the appliances into a list and add it to HA
    entities = []
    for device in home_connect.devices:
        # get a list of all switches
        switch_list = device.get_switches()
        for i in switch_list:
            # create a home connect switch
            switch = HomeConnectSwitch(i["device"], i["description"])
            # add switch to the list
            entities.append(switch)

    # add all entities to HA
    async_add_entities(entities, True)


class HomeConnectSwitch(HomeConnectEntity, SwitchEntity):
    """Switch class for Home Connect."""

    def __init__(self, device, description) -> None:
        """Initialize the entity."""

        super().__init__(device, description)
        self._state = None

    @property
    def is_on(self):
        """Return true if the switch is on."""

        return bool(self._state)

    async def async_turn_on(self, **kwargs):
        """Switch the device on."""

        _LOGGER.debug("Tried to switch on %s", self.name)

        try:
            # Start selected program if door is closed, remmote is enables and state is ready or finished
            if self._device.appliance.status["BSH.Common.Status.RemoteControlStartAllowed"].get("value") and self._device.appliance.status["BSH.Common.Status.DoorState"].get("value") in ["BSH.Common.EnumType.DoorState.Closed", "BSH.Common.EnumType.DoorState.Locked"] and self._device.appliance.status["BSH.Common.Status.OperationState"].get("value") in ["BSH.Common.EnumType.OperationState.Ready", "BSH.Common.EnumType.OperationState.Finished"]:
                program = self._device.appliance.status["BSH.Common.Root.SelectedProgram"].get("value")
                await self.hass.async_add_executor_job(self._device.appliance.set_programs_active, program)

            # Resume program if state if Pause
            elif self._device.appliance.status["BSH.Common.Status.OperationState"].get("value") == "BSH.Common.EnumType.OperationState.Pause":
                await self.hass.async_add_executor_job(self._device.appliance.set_command, "BSH.Common.Command.ResumeProgram")

        except HomeConnectError as err:
            _LOGGER.error("Error while trying to turn on device: %s", err)
            self._state = False

        self.async_entity_update()

    async def async_turn_off(self, **kwargs):
        """Switch the device off."""

        _LOGGER.debug("Tried to switch off %s", self.name)

        try:
            # Pause program if state is Run
            if self._device.appliance.status["BSH.Common.Status.OperationState"].get("value") == "BSH.Common.EnumType.OperationState.Run":
                await self.hass.async_add_executor_job(self._device.appliance.set_command, "BSH.Common.Command.PauseProgram")

        except HomeConnectError as err:  # pylint: disable=unused-variable
            _LOGGER.error("Error while trying to turn on device: %s", err)
            self._state = True

        self.async_entity_update()

    async def async_update(self):
        """Update the switch's status."""

        if self._device.appliance.status["BSH.Common.Status.OperationState"].get("value") in ["BSH.Common.EnumType.OperationState.Run", "BSH.Common.EnumType.OperationState.DelayedStart"]:
            self._state = True
        elif self._device.appliance.status["BSH.Common.Status.OperationState"].get("value") in ["BSH.Common.EnumType.OperationState.Ready", "BSH.Common.EnumType.OperationState.Finished", "BSH.Common.EnumType.OperationState.Pause", "BSH.Common.EnumType.OperationState.Inactive", "BSH.Common.EnumType.OperationState.ActionRequired", "BSH.Common.EnumType.OperationState.Error", "BSH.Common.EnumType.OperationState.Aborting"]:
            self._state = False
        else:
            self._state = None
        # _LOGGER.debug("Updated, new state: %s", self._state)
