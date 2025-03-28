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

from homeassistant.components.climate import ClimateEntity
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

ICON = "mdi:grill"

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Recteq climate entity from a config entry."""
    device = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RecteqClimate(entry, device)])

class RecteqClimate(ClimateEntity):
    """Representation of a Recteq grill climate entity."""

    def __init__(self, config_entry, device: RecteqDevice):
        """Initialize the climate entity."""
        super().__init__()
        self._config_entry = config_entry
        self._device = device
        self._grill_type = config_entry.data[CONF_GRILL_TYPE]
        self._dps = GRILL_MODELS[self._grill_type]  # Store grill-type-specific DPS
        self._temp_min = self._dps["TEMP_MIN"]  # e.g., 200°F
        self._temp_max = self._dps["TEMP_MAX"]  # e.g., 500°F
        self._low_mode_temp = self._dps["LOW_MODE_TEMP"]  # e.g., 180°F
        self._full_mode_temp = self._dps["FULL_MODE_TEMP"]  # e.g., 600°F
        self._attr_min_temp = self._low_mode_temp
        self._attr_max_temp = self._full_mode_temp
        self._attr_target_temperature_step = 5.0
        self._attr_target_temperature = None
        self._intended_target_temperature = None  # Track the intended temperature
        self._attr_current_temperature = None
        self._attr_hvac_mode = HVACMode.OFF

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
        temp = self._device.dps(self._dps["DPS_ACTUAL"])
        if temp is None:
            return None
        return round(float(self._device.temperature(temp)), 1)

    @property
    def target_temperature(self):
        """Return the target temperature."""
        temp = self._device.dps(self._dps["DPS_TARGET"])
        if temp is None:
            return None
        return round(float(self._device.temperature(temp)), 1)

    def set_temperature(self, **kwargs):
        """Set a new target temperature with snapping and jumping logic."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is not None:
            current_temp = self._attr_target_temperature
            step = self._attr_target_temperature_step

            if current_temp is not None:
                if temp < self._temp_min:
                    if temp == self._low_mode_temp:
                        _LOGGER.debug(f"Temp set directly to Low Mode")
                        pass  # Allow exact low_mode_temp
                    elif current_temp == self._temp_min and temp == self._temp_min - step:
                        _LOGGER.debug(f"Snap to Low Mode")
                        temp = self._low_mode_temp
                    else:
                        _LOGGER.debug(f"Snap to min temp")
                        temp = self._temp_min
                elif temp > self._temp_max:
                    if temp == self._full_mode_temp:
                        _LOGGER.debug(f"Temp set directly to Full Mode")
                        pass #Allow exact full_mode_temp
                    elif current_temp == self._temp_max and temp == self._temp_max + step:
                        _LOGGER.debug(f"Snap to Full Mode")
                        temp = self._full_mode_temp
                    else:
                        _LOGGER.debug(f"Snap to max temp")
                        temp = self._temp_max
                else:
                    _LOGGER.debug(f"No special temp requirement")
                    pass 

            # Set the temperature on the device
            self._device.dps(self._dps['DPS_TARGET'], int(temp + 0.5))
            # Update the entity's target temperature immediately
            self._attr_target_temperature = temp
            # Update the UI right away in a thread-safe manner
            self.hass.loop.call_soon_threadsafe(lambda: self.async_write_ha_state())

    def set_hvac_mode(self, hvac_mode):
        """Set the HVAC mode."""
        if hvac_mode == HVACMode.HEAT:
            self.turn_on()
        elif hvac_mode == HVACMode.OFF:
            self.turn_off()
        else:
            raise ValueError(f"Invalid hvac_mode: '{hvac_mode}'")

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
        self._device.dps(self._dps["DPS_POWER"], POWER_ON)

    def turn_off(self):
        """Turn the grill off."""
        self._device.dps(self._dps["DPS_POWER"], POWER_OFF)

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def min_temp(self):
        """Return the minimum temperature (low mode)."""
        return self._attr_min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature (full mode)."""
        return self._attr_max_temp

    @property
    def state_attributes(self):
        """Return the state attributes."""
        data = {ATTR_TEMPERATURE: self._attr_target_temperature}
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
            ATTR_TARGET_TEMP_STEP: self._attr_target_temperature_step,
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
        # Fetch initial state from the device
        await self._device.async_request_refresh()
        initial_target = self.target_temperature
        self._attr_target_temperature = initial_target
        self._intended_target_temperature = None  # No intended temp on startup
        self.async_write_ha_state()

    @callback
    def _update_callback(self):
        """Handle updates from the device."""
        new_target_temp = self.target_temperature
        _LOGGER.info(f"Device reported target temperature: {new_target_temp}°F")

        # Only update the entity's target temperature if it matches the intended
        # temperature or if no intended temperature is set
        if self._intended_target_temperature is None:
            self._attr_target_temperature = new_target_temp
        elif new_target_temp == self._intended_target_temperature:
            self._attr_target_temperature = new_target_temp
            self._intended_target_temperature = None  # Reset after confirmation
            _LOGGER.info(f"Device confirmed intended temperature: {new_target_temp}°F")
        else:
            _LOGGER.debug(
                f"Ignoring device update {new_target_temp}°F; "
                f"waiting for intended {self._intended_target_temperature}°F"
            )

        self.async_write_ha_state()