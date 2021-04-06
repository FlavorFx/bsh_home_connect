"""Home Connect API"""

import json
import logging
import os
import time
from threading import Event, Thread
from typing import Callable, Dict, Optional, Union
from oauthlib.oauth2 import TokenExpiredError
from requests import Response
from requests_oauthlib import OAuth2Session
from .sseclient import SSEClient
from .const import BASE_URL, ENDPOINT_APPLIANCES, ENDPOINT_TOKEN

_LOGGER = logging.getLogger("homeconnect")

TIMEOUT_S = 120


class watch_dog_timer:
    def __init__(self, time, callback):
        self.callback = callback
        self.time = time
        self.reset_event = Event()
        self.resume_event = Event()
        self.stopped_event = Event()
        self.pause_flag = False
        self.stop_flag = False
        self.start()

    def __del__(self):
        self.stop()

    def start(self):
        Thread(target=self.checker).start()

    def stop(self):
        self.stop_flag = True
        self.reset_event.set()
        self.stopped_event.wait()

    def reset(self):
        self.reset_event.set()

    def pause(self):
        self.pause_flag = True
        self.reset_event.set()

    def resume(self):
        self.pause_flag = False
        self.resume_event.set()

    def checker(self):
        while not self.stop_flag:
            if self.pause_flag:
                self.resume_event.wait()
                self.resume_event.clear()
            if self.reset_event.wait(self.time):
                self.reset_event.clear()
            else:
                self.callback()
        self.stopped_event.set()


class HomeConnectError(Exception):
    pass


class HomeConnectAPI:
    def __init__(self, token: Optional[Dict[str, str]] = None, client_id: str = None, client_secret: str = None, redirect_uri: str = None, token_updater: Optional[Callable[[str], None]] = None):
        self.host = BASE_URL
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_updater = token_updater

        extra = {"client_id": self.client_id, "client_secret": self.client_secret}

        self._oauth = OAuth2Session(client_id=client_id, redirect_uri=redirect_uri, auto_refresh_kwargs=extra, token=token, token_updater=token_updater)

    def refresh_tokens(self) -> Dict[str, Union[str, int]]:
        """Refresh and return new tokens."""

        _LOGGER.info("Refreshing tokens")
        token = self._oauth.refresh_token(f"{self.host}{ENDPOINT_TOKEN}")

        if self.token_updater is not None:
            self.token_updater(token)

        return token

    def request(self, method: str, path: str, **kwargs) -> Response:
        """Make a request. We don't use the built-in token refresh mechanism of OAuth2 session because we want to allow overriding the token refresh logic."""

        url = f"{self.host}{path}"
        try:
            return getattr(self._oauth, method)(url, **kwargs)

        except TokenExpiredError:
            _LOGGER.warning("Token expired.")
            self._oauth.token = self.refresh_tokens()

            return getattr(self._oauth, method)(url, **kwargs)

    def get(self, endpoint):
        """Get data as dictionary from an endpoint."""

        res = self.request("get", endpoint)

        if not res.content:
            return {}
        try:
            res = res.json()
        except:
            raise ValueError("Cannot parse {} as JSON".format(res))

        if "error" in res:
            raise HomeConnectError(res["error"])
        elif "data" not in res:
            raise HomeConnectError("Unexpected error")

        return res["data"]

    def put(self, endpoint, data):
        """Send (PUT) data to an endpoint."""

        res = self.request("put", endpoint, data=json.dumps(data), headers={"Content-Type": "application/vnd.bsh.sdk.v1+json", "accept": "application/vnd.bsh.sdk.v1+json"})

        if not res.content:
            return {}
        try:
            res = res.json()
        except:
            raise ValueError("Cannot parse {} as JSON".format(res))
        if "error" in res:
            raise HomeConnectError(res["error"])

        return res

    def delete(self, endpoint):
        """Delete an endpoint."""

        res = self.request("delete", endpoint)

        if not res.content:
            return {}
        try:
            res = res.json()
        except:
            raise ValueError("Cannot parse {} as JSON".format(res))

        if "error" in res:
            raise HomeConnectError(res["error"])
        return res

    def get_appliances(self):
        """Return a list of `HomeConnectAppliance` instances for all appliances."""

        data = self.get(ENDPOINT_APPLIANCES)

        return [HomeConnectAppliance(self, **app) for app in data["homeappliances"]]


class HomeConnectAppliance:
    """Class representing a single appliance."""

    def __init__(self, hc, haId, vib=None, brand=None, type=None, name=None, enumber=None, connected=False):
        self.hc = hc
        self.haId = haId
        self.vib = vib or ""
        self.brand = brand or ""
        self.type = type or ""
        self.name = name or ""
        self.enumber = enumber or ""
        self.is_connected = connected

        # Create and initialize messages, events and variables
        self.status = {}
        self.status["BSH.Common.Status.DoorState"] = {"value": None}
        self.status["BSH.Common.Status.RemoteControlStartAllowed"] = {"value": None}
        self.status["BSH.Common.Status.OperationState"] = {"value": None}
        self.status["BSH.Common.Option.ProgramProgress"] = {"value": 0}
        self.status["BSH.Common.Option.RemainingProgramTime"] = {"value": 0}
        self.status["BSH.Common.Root.SelectedProgram"] = {"value": None}
        self.status["LaundryCare.Washer.Option.Temperature"] = {"value": None}
        self.status["LaundryCare.Washer.Option.SpinSpeed"] = {"value": None}
        self.status["LaundryCare.Dryer.Option.DryingTarget"] = {"value": None}
        self.status["Cooking.Common.Setting.Lighting"] = {"value": None}
        self.status["Cooking.Common.Setting.LightingBrightness"] = {"value": None}
        self.status["BSH.Common.Setting.AmbientLightEnabled"] = {"value": None}
        self.status["BSH.Common.Setting.AmbientLightBrightness"] = {"value": None}
        self.status["BSH.Common.Setting.AmbientLightColor"] = {"value": None}
        self.status["BSH.Common.Setting.AmbientLightCustomColor"] = {"value": None}

        # Setup a watchdog and check every 5 minutes for a valid connection
        self.wdt = watch_dog_timer(300.0, self._observer)
        self.wdt.pause()

    def __repr__(self):
        return "HomeConnectAppliance(hc, haId='{}', vib='{}', brand='{}', type='{}', name='{}', enumber='{}', connected={})".format(self.haId, self.vib, self.brand, self.type, self.name, self.enumber, self.is_connected)

    @staticmethod
    def json2dict(lst):
        """Turn a list of dictionaries where one key is called 'key' into a dictionary with the value of 'key' as key."""
        return {d.pop("key"): d for d in lst}

    def update_properties(self):
        """Updates the status, settingds, programs, etc. of appliance."""

        # if there is an established connection, further requests can be retrieved
        if self.is_connected:

            # Update status
            try:
                self.update_status()
            except (HomeConnectError, ValueError) as err:  # pylint: disable=unused-variable
                _LOGGER.debug("Unable to fetch appliance status. %s", err)

            # Update settings
            try:
                self.update_settings()
            except (HomeConnectError, ValueError) as err:  # pylint: disable=unused-variable
                _LOGGER.debug("Unable to fetch appliance settings. %s", err)

            if self.type in ["Washer", "Dryer", "WasherDryer"]:
                # Get selected program
                try:
                    selected_program = self.get_programs_selected()
                    self.status["BSH.Common.Root.SelectedProgram"] = {"value": selected_program.get("key")}
                except (HomeConnectError, ValueError) as err:  # pylint: disable=unused-variable
                    _LOGGER.debug("Unable to fetch selected program. %s", err)

            if self.type in ["Washer", "WasherDryer"]:
                # Get temperature from selected program
                try:
                    temperature = self.get_programs_selected_options_with_key("LaundryCare.Washer.Option.Temperature")["value"]
                    self.status["LaundryCare.Washer.Option.Temperature"] = {"value": temperature}
                except (HomeConnectError, ValueError) as err:  # pylint: disable=unused-variable
                    _LOGGER.debug("Unable to fetch selected program. %s", err)
                # Get spin speed from selected program
                try:
                    spin_speed = self.get_programs_selected_options_with_key("LaundryCare.Washer.Option.SpinSpeed")["value"]
                    self.status["LaundryCare.Washer.Option.SpinSpeed"] = {"value": spin_speed}
                except (HomeConnectError, ValueError) as err:  # pylint: disable=unused-variable
                    _LOGGER.debug("Unable to fetch selected program. %s", err)

            if self.type in ["Dryer", "WasherDryer"]:
                # Get selected drying target
                try:
                    drying_target = self.get_programs_selected_options_with_key("LaundryCare.Dryer.Option.DryingTarget")["value"]
                    self.status["LaundryCare.Dryer.Option.DryingTarget"] = {"value": drying_target}
                except (HomeConnectError, ValueError) as err:  # pylint: disable=unused-variable
                    _LOGGER.debug("Unable to fetch drying target. %s", err)

            # Watchdog counter resume because there is a valid connection
            self.wdt.resume()

    def listen_events(self, callback=None):
        """Spawn a thread with an event listener that updates the status."""
        uri = f"{self.hc.host}/api/homeappliances/{self.haId}/events"
        sse = SSEClient(uri, session=self.hc._oauth, retry=1000, timeout=TIMEOUT_S)
        Thread(target=self._listen, args=(sse, callback)).start()

    def _listen(self, sse, callback=None):
        """Worker function for listener."""

        _LOGGER.info("Listening to event stream for device %s", self.name)

        try:
            for event in sse:
                _LOGGER.debug("Handle event: %s", event.event)

                if event.event == "NOTIFY":  # e.g. Progress update
                    # set home connect applieance to connected
                    self.is_connected = True
                    # load event data
                    event = json.loads(event.data)
                    # convert mqtt message to dictinary
                    d = self.json2dict(event["items"])
                    # store and update all messages of this appliance in status to get access from home assistance entities
                    self.status.update(d)
                    # call callback function from home assistance home connect devices class
                    if callback is not None:
                        callback(self)
                    # Watchdog counter reset
                    self.wdt.reset()

                elif event.event == "STATUS":  # e.g. Program selection
                    # set home connect applieance to connected
                    self.is_connected = True
                    # load event data
                    event = json.loads(event.data)
                    # convert mqtt message to dictinary
                    d = self.json2dict(event["items"])
                    # store and update all messages of this appliance in status to get access from home assistance entities
                    self.status.update(d)
                    # call callback function from home assistance home connect devices class
                    if callback is not None:
                        callback(self)
                    # Watchdog counter reset
                    self.wdt.reset()

                elif event.event == "EVENT":  # e.g. Program finished
                    # set home connect applieance to connected
                    self.is_connected = True
                    # load event data
                    event = json.loads(event.data)
                    # convert mqtt message to dictinary
                    d = self.json2dict(event["items"])
                    # store and update all messages of this appliance in status to get access from home assistance entities
                    self.status.update(d)
                    # when program is finished set ProgramProgress to 100% and RemainingProgramTime to 0s
                    if "BSH.Common.Event.ProgramFinished" in d and d.get("BSH.Common.Event.ProgramFinished")["value"] == "BSH.Common.EnumType.EventPresentState.Present":
                        self.status.get("BSH.Common.Option.ProgramProgress")["value"] = 100
                        self.status.get("BSH.Common.Option.RemainingProgramTime")["value"] = 0
                    # call callback function from home assistance home connect devices class
                    if callback is not None:
                        callback(self)
                    # Watchdog counter reset
                    self.wdt.reset()

                elif event.event == "CONNECTED":
                    # set home connect applieance to connected
                    self.is_connected = True
                    # update aplienace properties like Seleced Program, Spin speed, etc.
                    self.update_properties()
                    # call callback function from home assistance home connect devices class
                    if callback is not None:
                        callback(self)
                    # Watchdog counter resume because there is a valid connection
                    self.wdt.resume()

                elif event.event == "DISCONNECTED":
                    # set home connect applieance to disconnected
                    self.is_connected = False
                    # call callback function from home assistance home connect devices class
                    if callback is not None:
                        callback(self)
                    # Watchdog pause
                    self.wdt.pause()

                elif event.event == "KEEP-ALIVE":
                    # Watchdog counter reset
                    self.wdt.reset()

                else:
                    _LOGGER.error("Invalid event type: %s", event.event)

        except TokenExpiredError as err:  # pylint: disable=unused-variable
            _LOGGER.info("Token expired in event stream.")

            self.hc._oauth.token = self.hc.refresh_tokens()
            uri = f"{self.hc.host}/api/homeappliances/{self.haId}/events"
            sse = SSEClient(uri, session=self.hc._oauth, retry=1000, timeout=TIMEOUT_S)
            self._listen(sse, callback=callback)

        except Exception as err:
            _LOGGER.error("Unhandled exception occured. %s", err)

    def _observer(self):
        """Recover the connection when it's lost."""
        _LOGGER.error("Server connection lost")

    def get(self, endpoint):
        """Get data (as dictionary) from an endpoint."""
        return self.hc.get("{}/{}{}".format(ENDPOINT_APPLIANCES, self.haId, endpoint))

    def put(self, endpoint, data):
        """Send (PUT) data to an endpoint."""
        return self.hc.put("{}/{}{}".format(ENDPOINT_APPLIANCES, self.haId, endpoint), data)

    def delete(self, endpoint):
        """Delete endpoint."""
        return self.hc.delete("{}/{}{}".format(ENDPOINT_APPLIANCES, self.haId, endpoint))

    def get_programs(self):
        """Get a list of all programs."""

        programs = self.get("/programs")

        if not programs or "programs" not in programs:
            return []

        return [p["key"] for p in programs["programs"]]

    def get_programs_available(self):
        """Get a list of available programs."""

        programs = self.get("/programs/available")

        if not programs or "programs" not in programs:
            return []

        return [p["key"] for p in programs["programs"]]

    def get_programs_available_with_key(self, program_key):
        """Get program options."""

        options = self.get(f"/programs/available/{program_key}")

        if not options or "options" not in options:
            return []

        return [{p["key"]: p} for p in options["options"]]

    def get_programs_active(self):
        """Get the active program."""
        return self.get("/programs/active")

    def get_programs_active_options(self):
        """List of options of active program."""
        return self.get("/programs/active/options")

    def get_programs_active_options_with_key(self, option_key):
        """Option of active program."""
        return self.get(f"/programs/active/options/{option_key}")

    def get_programs_selected(self):
        """Get the selected program."""
        return self.get("/programs/selected")

    def get_programs_selected_options(self):
        """List of options of selected program."""
        return self.get("/programs/selected/options")

    def get_programs_selected_options_with_key(self, option_key):
        """Option of selected program."""
        return self.get(f"/programs/selected/options/{option_key}")

    def set_programs_active(self, program_key, options=None):
        """Start the given program."""

        if options is not None:
            return self.put("/programs/active", {"data": {"key": program_key, "options": options}})

        return self.put("/programs/active", {"data": {"key": program_key}})

    def set_programs_active_options(self, options):
        """Set all options of the active program, e.g. to switch from preheating to the actual program options."""
        return self.put("/programs/active/options", {"data": {"options": options}})

    def set_programs_active_options_with_key(self, option_key, value, unit=None):
        """Set one specific option of the active program."""

        if unit is not None:
            return self.put(f"/programs/active/options/{option_key}", {"data": {"key": option_key, "value": value, "unit": unit}})

        return self.put(f"/programs/active/options/{option_key}", {"data": {"key": option_key, "value": value}})

    def stop_programs_active(self, value):
        """Stop the program which is currently executed."""
        return self.delete("/programs/active")

    def set_programs_selected(self, program_key, options=None):
        """Select a program."""

        if options is not None:
            return self.put("/programs/selected", {"data": {"key": program_key, "options": options}})

        return self.put("/programs/selected", {"data": {"key": program_key}})

    def set_programs_selected_options(self, options):
        """Set all options of selected program."""
        return self.put("/programs/selected/options", {"data": {"options": options}})

    def set_programs_selected_options_with_key(self, option_key, value, unit=None):
        """Set specific option of selected program."""

        if unit is not None:
            return self.put(f"/programs/selected/options/{option_key}", {"data": {"key": option_key, "value": value, "unit": unit}})

        return self.put(f"/programs/selected/options/{option_key}", {"data": {"key": option_key, "value": value}})

    def update_status(self):
        """Get the status (as dictionary) and update `self.status`."""

        status = self.get("/status")

        if not status or "status" not in status:
            return {}

        # Update the status dictunary
        self.status.update(self.json2dict(status["status"]))

        return self.status

    def get_status_with_key(self, status_key):
        """Get current status of home appliance."""
        return self.get(f"/status/{status_key}")

    def update_settings(self):
        """Get a list of available settings."""

        settings = self.get("/settings")

        if not settings or "settings" not in settings:
            return {}

        # Update the status dictunary
        self.status.update(self.json2dict(settings["settings"]))

        return self.status

    def get_settings_with_key(self, setting_key):
        """Get a specific setting"""
        return self.get(f"/settings/{setting_key}")

    def set_settings_with_key(self, setting_key, value):
        """Change the current setting of `setting_key`."""
        return self.put("/settings/{}".format(setting_key), {"data": {"key": setting_key, "value": value}})

    def get_commands(self):
        """Get a list of supported commands of the home appliance."""
        return self.get("/commands")

    def set_command(self, command_key):
        """Execute a specific command of the home appliance."""
        return self.put(f"/commands/{command_key}", {"data": {"key": command_key, "value": True}})
