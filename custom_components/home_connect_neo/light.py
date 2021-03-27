"""Light Sensor for Home Connect"""

import logging
from math import ceil
from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_HS_COLOR, LightEntity  # pylint: disable=import-error, no-name-in-module
from homeassistant.util import color as color_util  # pylint: disable=import-error, no-name-in-module
from .const import DOMAIN, SIGNAL_UPDATE_ENTITIES
from .entity import HomeConnectEntity
from .homeconnect import HomeConnectError

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add switch sensor in HA."""

    home_connect = hass.data[DOMAIN][config_entry.entry_id]

    # put all lights of the appliances into a list and add it to HA
    entities = []
    for device in home_connect.devices:
        # get a list of all lights
        lichts_list = device.get_lights()
        for i in lichts_list:
            # create a home connect light
            light = HomeConnectLight(i["device"], i["key"], i["description"])
            # add light to the list
            entities.append(light)

    # add all entities to HA
    async_add_entities(entities, True)


class HomeConnectLight(HomeConnectEntity, LightEntity):
    """Light class for Home Connect."""

    def __init__(self, device, key, description) -> None:
        """Initialize entity."""
        super().__init__(device, description)
        self._key = key
        self._state = None
        self._brightness = None
        self._hs_color = None

    @property
    def is_on(self):
        """Return true if light is on."""
        return bool(self._state)

    @property
    def brightness(self):
        """Return the brightness of light."""
        return self._brightness

    @property
    def hs_color(self):
        """Returns the color of  light."""
        return self._hs_color

    async def async_turn_on(self, **kwargs):
        """Switch  light on."""

        if self._key == "BSH.Common.Setting.AmbientLightEnabled":
            # Turn on ambient light
            try:
                await self.hass.async_add_executor_job(self.device.appliance.set_setting, self._key, True)
            except HomeConnectError as err:
                _LOGGER.error("Error while trying to turn on ambient light: %s", err)
                return

            # Set hue and saturation and brightness of ambient light
            if ATTR_BRIGHTNESS in kwargs or ATTR_HS_COLOR in kwargs:
                try:
                    await self.hass.async_add_executor_job(self.device.appliance.set_setting, "BSH.Common.Setting.AmbientLightColor", "BSH.Common.EnumType.AmbientLightColor.CustomColor")
                except HomeConnectError as err:
                    _LOGGER.error("Error while trying selecting customcolor: %s", err)

                if self._brightness is not None:
                    # Set brightness
                    if ATTR_BRIGHTNESS in kwargs:
                        brightness = 10 + ceil(kwargs[ATTR_BRIGHTNESS] / 255 * 90)
                    else:
                        brightness = 10 + ceil(self._brightness / 255 * 90)

                    # Set hue and saturation
                    hs_color = kwargs.get(ATTR_HS_COLOR, self._hs_color)
                    if hs_color is not None:
                        rgb = color_util.color_hsv_to_RGB(*hs_color, brightness)
                        hex_val = color_util.color_rgb_to_hex(rgb[0], rgb[1], rgb[2])
                        try:
                            await self.hass.async_add_executor_job(self.device.appliance.set_setting, "BSH.Common.Setting.AmbientLightCustomColor", f"#{hex_val}")
                        except HomeConnectError as err:
                            _LOGGER.error("Error while trying setting the color: %s", err)

        elif self._key == "Cooking.Common.Setting.Lighting":
            if ATTR_BRIGHTNESS in kwargs:
                # Set brightness of functional light
                brightness = 10 + ceil(kwargs[ATTR_BRIGHTNESS] / 255 * 90)
                try:
                    await self.hass.async_add_executor_job(self.device.appliance.set_setting, "Cooking.Common.Setting.LightingBrightness", brightness)
                except HomeConnectError as err:
                    _LOGGER.error("Error while trying set the brightness: %s", err)
            else:
                # Turn on functional light
                try:
                    await self.hass.async_add_executor_job(self.device.appliance.set_setting, self._key, True)
                except HomeConnectError as err:
                    _LOGGER.error("Error while trying to turn on light: %s", err)

        else:
            _LOGGER.warning("Unexpected value for key: %s", self._key)

        self.async_entity_update()

    async def async_turn_off(self, **kwargs):
        """Switch light off."""
        try:
            await self.hass.async_add_executor_job(self.device.appliance.set_settings_with_key, self._key, False)
        except HomeConnectError as err:
            _LOGGER.error("Error while trying to turn off light: %s", err)
        self.async_entity_update()

    async def async_update(self):
        """Update light's status."""

        # get all messages of this appliance stored in status
        status = self._device.appliance.status

        # check if a message has been received already
        if self._key not in status:
            self._state = None
        elif "value" not in status[self._key]:
            self._state = None
        else:
            # Functional or ambient lighting
            if self._key in ["BSH.Common.Setting.AmbientLightEnabled", "Cooking.Common.Setting.Lighting"]:
                self._state = status[self._key].get("value") == "true"

            # Functional lighting
            if self._key == "Cooking.Common.Setting.Lighting":

                # Brightness
                brightness = self.device.appliance.status.get("Cooking.Common.Setting.LightingBrightness", {})
                if brightness is not None:
                    self._brightness = ceil((brightness.get("value") - 10) * 255 / 90)
                else:
                    self._brightness = None

            # Ambient lighting
            elif self._key == "BSH.Common.Setting.AmbientLightEnabled":

                # Brightness
                brightness = self.device.appliance.status.get("BSH.Common.Setting.AmbientLightBrightness", {})
                if brightness is not None:
                    self._brightness = ceil((brightness.get("value") - 10) * 255 / 90)
                else:
                    self._brightness = None

                # Hue, saturation and brightness for custom color
                color = self.device.appliance.status.get("BSH.Common.Setting.AmbientLightCustomColor", {})
                if color is not None:
                    colorvalue = color.get("value")[1:]
                    rgb = color_util.rgb_hex_to_rgb_list(colorvalue)
                    hsv = color_util.color_RGB_to_hsv(rgb[0], rgb[1], rgb[2])
                    self._hs_color = [hsv[0], hsv[1]]
                    self._brightness = ceil((hsv[2] - 10) * 255 / 90)
                else:
                    self._hs_color = None
                    self._brightness = None

            else:
                _LOGGER.warning("Unexpected value for key: %s", self._key)