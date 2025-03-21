"""Constants for the Recteq integration."""

import homeassistant.const as hac

DOMAIN = 'recteq'

PLATFORMS = ['climate', 'sensor']

DPS_POWER  = '1'
DPS_TARGET = '101'
DPS_ACTUAL = '102'
DPS_PROBEA = '103' # RT700 uses 103, newer grills must use 104
DPS_PROBEB = '104' # RT700 uses 104, newer grills must use 105

ATTR_POWER  = 'power'   # read/write
ATTR_TARGET = 'target'  # read/write
ATTR_ACTUAL = 'actual'  # read-only
ATTR_PROBEA = 'probe_a' # read-only
ATTR_PROBEB = 'probe_b' # read-only

POWER_ON  = True
POWER_OFF = False

PROTOCOL_3_1 = '3.1'
PROTOCOL_3_3 = '3.3'
PROTOCOL_3_4 = '3.4'

PROTOCOLS = [PROTOCOL_3_1, PROTOCOL_3_3, PROTOCOL_3_4]

LEN_DEVICE_ID = 22
LEN_LOCAL_KEY = 16

CONF_NAME             = hac.CONF_NAME
CONF_IP_ADDRESS       = hac.CONF_IP_ADDRESS
CONF_DEVICE_ID        = 'device_id'
CONF_LOCAL_KEY        = 'local_key'
CONF_PROTOCOL         = 'protocol'
CONF_FORCE_FAHRENHEIT = 'force_fahrenheit'

DEFAULT_PROTOCOL = PROTOCOL_3_3

STR_INVALID_PREFIX = 'invalid_'
STR_PLEASE_CORRECT = 'please_correct'

FORCE_FAHRENHEIT = True
