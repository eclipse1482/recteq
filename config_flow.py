"""Config flow for the Recteq integration."""

import socket
import uuid
import voluptuous as vol
from homeassistant.helpers.selector import selector  # Import selector for dropdown support

from .const import (
    CONF_DEVICE_ID, CONF_IP_ADDRESS, CONF_LOCAL_KEY, CONF_NAME, CONF_PROTOCOL,
    CONF_GRILL_TYPE, GRILL_TYPES, DEFAULT_GRILL_TYPE, CONF_FORCE_FAHRENHEIT,
    DEFAULT_PROTOCOL, DOMAIN, LEN_DEVICE_ID, LEN_LOCAL_KEY, PROTOCOLS,
    STR_INVALID_PREFIX, STR_PLEASE_CORRECT,
)
from collections import OrderedDict
from homeassistant import config_entries
from homeassistant.core import callback

@config_entries.HANDLERS.register(DOMAIN)
class RecteqFlowHandler(config_entries.ConfigFlow):
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        self._errors = {}
        self._data = {}

    async def async_step_user(self, user_input=None):
        self._errors = {}

        if user_input is not None:
            self._data.update(user_input)

            try:
                socket.inet_aton(user_input[CONF_IP_ADDRESS])
            except socket.error:
                self._errors[CONF_IP_ADDRESS] = STR_INVALID_PREFIX + CONF_IP_ADDRESS

            user_input[CONF_DEVICE_ID] = user_input[CONF_DEVICE_ID].replace(" ", "")
            if len(user_input[CONF_DEVICE_ID]) > LEN_DEVICE_ID:
                self._errors[CONF_DEVICE_ID] = STR_INVALID_PREFIX + CONF_DEVICE_ID

            user_input[CONF_LOCAL_KEY] = user_input[CONF_LOCAL_KEY].replace(" ", "")
            if len(user_input[CONF_LOCAL_KEY]) != LEN_LOCAL_KEY:
                self._errors[CONF_LOCAL_KEY] = STR_INVALID_PREFIX + CONF_LOCAL_KEY

            user_input[CONF_PROTOCOL] = user_input[CONF_PROTOCOL].strip()
            if user_input[CONF_PROTOCOL] not in PROTOCOLS:
                self._errors[CONF_PROTOCOL] = STR_INVALID_PREFIX + CONF_PROTOCOL

            existing_entries = self.hass.config_entries.async_entries(DOMAIN)
            for entry in existing_entries:
                if entry.data[CONF_DEVICE_ID] == user_input[CONF_DEVICE_ID]:
                    self._errors["base"] = "device_id_already_configured"
                    break

            if not self._errors:
                return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)
            else:
                self._errors["base"] = STR_PLEASE_CORRECT

        return await self._show_user_form(user_input)

    async def _show_user_form(self, user_input):
        name = ''
        ip_address = ''
        device_id = ''
        local_key = ''
        protocol = DEFAULT_PROTOCOL
        grill_type = DEFAULT_GRILL_TYPE

        if user_input is not None:
            if CONF_NAME in user_input:
                name = user_input[CONF_NAME]
            if CONF_IP_ADDRESS in user_input:
                ip_address = user_input[CONF_IP_ADDRESS]
            if CONF_DEVICE_ID in user_input:
                device_id = user_input[CONF_DEVICE_ID]
            if CONF_LOCAL_KEY in user_input:
                local_key = user_input[CONF_LOCAL_KEY]
            if CONF_PROTOCOL in user_input:
                protocol = user_input[CONF_PROTOCOL]
            if CONF_GRILL_TYPE in user_input:
                grill_type = user_input[CONF_GRILL_TYPE]

        data_schema = OrderedDict()
        data_schema[vol.Required(CONF_NAME, default=name)] = str
        data_schema[vol.Required(CONF_IP_ADDRESS, default=ip_address)] = str
        data_schema[vol.Required(CONF_DEVICE_ID, default=device_id)] = str
        data_schema[vol.Required(CONF_LOCAL_KEY, default=local_key)] = str
        # Use selector to force protocol type as a dropdown
        data_schema[vol.Required(CONF_PROTOCOL, default=protocol)] = selector({
            "select": {
                "options": PROTOCOLS,
                "mode": "dropdown"
            }
        })
        # Use selector to force grill type as a dropdown
        data_schema[vol.Required(CONF_GRILL_TYPE, default=grill_type)] = selector({
            "select": {
                "options": GRILL_TYPES,  # Assuming GRILL_TYPES is a list like ['RT590', 'RT700']
                "mode": "dropdown"       # Explicitly set to dropdown
            }
        })

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=self._errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=self.config_entry.data[CONF_NAME],
                data=user_input
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_FORCE_FAHRENHEIT,
                        default=self.config_entry.options.get(CONF_FORCE_FAHRENHEIT, False)
                    ): bool
                }
            ),
        )