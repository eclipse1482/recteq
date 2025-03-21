"""[The Recteq integration."""

import logging
import tinytuya
import async_timeout
import asyncio

from datetime import timedelta
from time import time
from threading import Lock

from .const import (
    CONF_DEVICE_ID,
    CONF_FORCE_FAHRENHEIT,
    CONF_IP_ADDRESS,
    CONF_LOCAL_KEY,
    CONF_NAME,
    CONF_PROTOCOL,
    DPS_POWER,
)

from homeassistant.helpers import update_coordinator

_LOGGER = logging.getLogger(__name__)

CACHE_SECONDS = 5
UPDATE_INTERVAL_ONLINE = timedelta(seconds=10)  # 10-second interval when online
UPDATE_INTERVAL_OFFLINE = timedelta(seconds=60) # 60-second delay after 3 failures

class RecteqDevice(update_coordinator.DataUpdateCoordinator):

    def __init__(self, hass, entry):
        """Initialize the Recteq device."""
        super().__init__(
            hass,
            _LOGGER,
            name=entry.data[CONF_NAME],
            update_interval=UPDATE_INTERVAL_ONLINE,
        )

        self._device_id = entry.data[CONF_DEVICE_ID]
        self._ip_address = entry.data[CONF_IP_ADDRESS]
        self._local_key = entry.data[CONF_LOCAL_KEY]
        self._protocol = entry.data[CONF_PROTOCOL]
        self._force_fahrenheit = entry.options.get(CONF_FORCE_FAHRENHEIT, False)
        _LOGGER.debug("force_fahrenheit is {}".format(self._force_fahrenheit))

        self._pytuya = tinytuya.OutletDevice(self._device_id, self._ip_address, self._local_key)
        self._pytuya.set_version(float(self._protocol))
        self._pytuya.set_socketTimeout(2)  # 2-second socket timeout

        self._cached_status = None
        self._cached_status_time = None
        self._consecutive_failures = 0  # Initialize consecutive failure counter

        self._units = hass.config.units
        self._lock = Lock()
        self._unsub = entry.add_update_listener(async_update_listener)

    def __del__(self):
        """Clean up by unsubscribing from entry updates."""
        self._unsub()

    @property
    def device_id(self):
        return self._device_id

    @property
    def ip_address(self):
        return self._ip_address

    @property
    def local_key(self):
        return self._local_key

    @property
    def force_fahrenheit(self):
        return self._force_fahrenheit

    @property
    def available(self):
        return self._cached_status is not None

    @property
    def is_on(self):
        return self.dps(DPS_POWER)

    @property
    def is_off(self):
        return not self.is_on

    def dps(self, dps, value=None):
        """Get or set a DPS value."""
        if value is None:
            if self._cached_status is None:
                return None
            return self._cached_status.get(dps)
        else:
            _LOGGER.debug("set {}={}".format(int(dps), value))
            try:
                result = self._pytuya.set_status(value, dps)
                if result:  # Command succeeded, reset failures and interval
                    self._consecutive_failures = 0
                    self.update_interval = UPDATE_INTERVAL_ONLINE
                    _LOGGER.debug("Command sent successfully, update interval reset to 10 seconds")
                return result
            except Exception as e:
                _LOGGER.error(f"Failed to send command: {e}")
                raise

    @property
    def units(self):
        return self._units

    @property
    def temperature_unit(self):
        if self._force_fahrenheit:
            return True
        return self.units.temperature_unit

    def temperature(self, degrees_f):
        return degrees_f

    def update(self):
        """Update device status with a single attempt."""
        self._lock.acquire()
        try:
            now = time()
            if not self._cached_status or now - self._cached_status_time > CACHE_SECONDS:
                status = self._pytuya.status()
                self._cached_status = status.get('dps') if status else None
                self._cached_status_time = time()
                if self._cached_status:
                    _LOGGER.debug("Updated status: {}".format(self._cached_status))
                else:
                    raise ConnectionError("No DPS data received, device may be offline")
        except ConnectionError as err:
            self._cached_status = None
            self._cached_status_time = time()
            _LOGGER.debug("Status update failed: {}".format(err))
            raise
        finally:
            self._lock.release()

    async def async_update(self):
        """Run update in the executor."""
        await self.hass.async_add_executor_job(self.update)

    async def _async_update_data(self):
        """Fetch data and adjust update interval based on failures."""
        try:
            async with async_timeout.timeout(5):
                await self.async_update()
            self._consecutive_failures = 0
            self.update_interval = UPDATE_INTERVAL_ONLINE
            _LOGGER.debug("Device online, update interval set to 10 seconds")
            return self._cached_status
        except (ConnectionError, asyncio.TimeoutError) as e:
            self._consecutive_failures += 1
            if self._consecutive_failures >= 3:
                self.update_interval = UPDATE_INTERVAL_OFFLINE
                _LOGGER.debug("Three consecutive failures, next update interval is 60 seconds")
            else:
                self.update_interval = UPDATE_INTERVAL_ONLINE
                _LOGGER.debug("Update failed, but less than three failures, keeping 10 seconds")
            raise update_coordinator.UpdateFailed(f"Device is offline: {e}")

async def async_update_listener(hass, entry):
    """Handle updates to the config entry."""
    device = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug("update entry: data={} options={}".format(entry.data, entry.options))
    device._force_fahrenheit = entry.options.get(CONF_FORCE_FAHRENHEIT, False)
    _LOGGER.debug("force_fahrenheit now {}".format(device.force_fahrenheit))