"""The Recteq sensor component."""

from .const import (
    DOMAIN,
    GRILL_MODELS,
    CONF_GRILL_TYPE,
)

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import callback
from homeassistant.helpers import entity

async def async_setup_entry(hass, entry, add):
    """Set up the Recteq sensor entities from a config entry."""
    device = hass.data[DOMAIN][entry.entry_id]
    grill_type = entry.data[CONF_GRILL_TYPE]
    dps = GRILL_MODELS[grill_type]  # Get grill-type-specific DPS values

    add(
        [
            RecteqSensor(device, dps['DPS_TARGET'], 'Target Temperature'),
            RecteqSensor(device, dps['DPS_ACTUAL'], 'Actual Temperature'),
            RecteqSensor(device, dps['DPS_PROBEA'], 'Probe A Temperature'),
            RecteqSensor(device, dps['DPS_PROBEB'], 'Probe B Temperature'),
        ]
    )

class RecteqSensor(entity.Entity):
    """Representation of a Recteq sensor entity."""

    def __init__(self, device, dps_key, name):
        """Initialize the sensor entity."""
        self._device = device
        self._dps_key = dps_key  # Store the DPS key (e.g., '101', '102')
        self._name = f"{device.name} {name}"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return f"{self._device.device_id}.{self._dps_key}"

    @property
    def available(self):
        """Return True if the sensor is available."""
        return self._device.available and self._device.is_on

    @property
    def state(self):
        """Return the current state of the sensor."""
        if not self.available:
            return STATE_UNAVAILABLE

        value = self._device.dps(self._dps_key)
        if value is None or value == 0:
            return STATE_UNAVAILABLE

        return round(float(self._device.temperature(value)), 1)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        if self._device.force_fahrenheit:
            return None
        return self._device.temperature_unit

    @property
    def device_class(self):
        """Return the device class."""
        return SensorDeviceClass.TEMPERATURE

    @property
    def should_poll(self):
        """Return True if polling is needed (False here as we use callbacks)."""
        return False

    async def async_update(self):
        """Update the sensor state."""
        await self._device.async_request_refresh()

    async def async_added_to_hass(self):
        """Handle entity addition to Home Assistant."""
        self.async_on_remove(self._device.async_add_listener(self._update_callback))

    @callback
    def _update_callback(self):
        """Handle updates from the device."""
        self.async_write_ha_state()