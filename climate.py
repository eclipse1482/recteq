"""The Recteq climate component."""

import logging

from .const import (
    DOMAIN,
    POWER_OFF,
    POWER_ON,
    GRILL_MODELS,
    CONF_GRILL_TYPE,
)
from .device import RecteqDevice

from homeassistant.components import climate
from homeassistant.components.climate.const import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_HVAC_MODE,
    ATTR_HVAC_MODES,
    ATTR_MAX_TEMP,
    ATTR_MIN_TEMP,
    ATTR_TARGET_TEMP_STEP,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_WHOLE,
    STATE_UNAVAILABLE,
)
from homeassistant.core import callback

_LOGGER = logging.getLogger(__name__)

ICON = 'mdi:grill'

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Recteq climate entity from a config entry."""
    device = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RecteqClimate(entry, device)])

class RecteqClimate(climate.ClimateEntity):
    """Representation of a Recteq grill climate entity."""

    def __init__(self, config_entry, device: RecteqDevice):
        """Initialize the climate entity."""
        super().__init__()
        self._config_entry = config_entry
        self._device = device
        self._grill_type = config_entry.data[CONF_GRILL_TYPE]
        self._dps = GRILL_MODELS[self._grill_type]  # Store grill-type-specific DPS
        self._temp_min = self._dps['TEMP_MIN']
        self._temp_max = self._dps['TEMP_MAX']

    @property
    def name(self):
        """Return the name of the device."""
        return self._device.name

    @property
    def unique_id(self):
        """Return a unique ID for the entity."""
        return self._device.device_id

    @property
    def icon(self):
        """Return the icon for the entity."""
        return ICON

    @property
    def available(self):
        """Return True if the entity is available."""
        return self._device.available

    @property
    def precision(self):
        """Return the precision of the temperature."""
        return PRECISION_WHOLE

    @property
    def temperature_unit(self):
        """Return the unit of temperature."""
        return self._device.temperature_unit

    @property
    def hvac_mode(self):
        """Return the current HVAC mode."""
        if self.is_on:
            return HVACMode.HEAT
        return HVACMode.OFF

    @property
    def hvac_modes(self):
        """Return the list of supported HVAC modes."""
        return [HVACMode.OFF, HVACMode.HEAT]

    @property
    def current_temperature(self):
        """Return the current temperature."""
        temp = self._device.dps(self._dps['DPS_ACTUAL'])
        if temp is None:
            return None
        return round(float(self._device.temperature(temp)), 1)

    @property
    def target_temperature(self):
        """Return the target temperature."""
        temp = self._device.dps(self._dps['DPS_TARGET'])
        if temp is None:
            return None
        return round(float(self._device.temperature(temp)), 1)

    @property
    def target_temperature_step(self):
        """Return the target temperature step."""
        # TODO: Could be made grill-type-specific via GRILL_MODELS
        return 5.0

    @property
    def target_temperature_high(self):
        """Return the highest allowable target temperature."""
        return self.max_temp

    @property
    def target_temperature_low(self):
        """Return the lowest allowable target temperature."""
        return self.min_temp

    def set_temperature(self, **kwargs):
        """Set a new target temperature."""
        mode = kwargs.get(ATTR_HVAC_MODE)
        if mode is not None:
            self.set_hvac_mode(mode)
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is not None:
            self._device.dps(self._dps['DPS_TARGET'], int(temp + 0.5))

    def set_hvac_mode(self, hvac_mode):
        """Set the HVAC mode."""
        if hvac_mode == HVACMode.HEAT:
            self.turn_on()
        elif hvac_mode == HVACMode.OFF:
            self.turn_off()
        else:
            raise ValueError(f'Invalid hvac_mode: "{hvac_mode}"')

    @property
    def is_on(self):
        """Return True if the grill is on."""
        return self._device.is_on

    @property
    def is_off(self):
        """Return True if the grill is off."""
        return self._device.is_off

    def turn_on(self):
        """Turn the grill on."""
        self._device.dps(self._dps['DPS_POWER'], POWER_ON)

    def turn_off(self):
        """Turn the grill off."""
        self._device.dps(self._dps['DPS_POWER'], POWER_OFF)

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return round(self._device.temperature(self._temp_min), 1)

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return round(self._device.temperature(self._temp_max), 1)

    @property
    def state_attributes(self):
        """Return the state attributes."""
        data = {ATTR_TEMPERATURE: self.target_temperature}
        if self.is_on:
            data[ATTR_CURRENT_TEMPERATURE] = self.current_temperature
        else:
            data[ATTR_CURRENT_TEMPERATURE] = STATE_UNAVAILABLE
        return data

    @property
    def capability_attributes(self):
        """Return the capability attributes."""
        return {
            ATTR_HVAC_MODES: self.hvac_modes,
            ATTR_MIN_TEMP: self.min_temp,
            ATTR_MAX_TEMP: self.max_temp,
            ATTR_TARGET_TEMP_STEP: self.target_temperature_step,
        }

    @property
    def should_poll(self):
        """Return True if polling is needed (False here as we use callbacks)."""
        return False

    async def async_update(self):
        """Update the entity state."""
        await self._device.async_request_refresh()

    async def async_added_to_hass(self):
        """Handle entity addition to Home Assistant."""
        self.async_on_remove(self._device.async_add_listener(self._update_callback))

    @callback
    def _update_callback(self):
        """Handle updates from the device."""
        self.async_write_ha_state()

# TODO Support "Max Smoke" Mode
#   The recteq app sets the target temperature to 180 when it's on TEMP_MIN
#   and the user taps the "-" button one more time.

# TODO Support "Full" Mode
#   The recteq app sets the target temperature to 600 when it's on TEMP_MAX
#   and the user taps the "+" button one more time.