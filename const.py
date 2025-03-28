"""Constants for the Recteq integration."""

import homeassistant.const as hac

# These points are required by the HACS integration
PROJECT = 'Recteq Custom Integration'
VERSION_TUPLE = (1, 0, 0)
VERSION = __version__ = '%d.%d.%d' % VERSION_TUPLE
__author__ = 'Paul Dugas <paul@dugas.cc>'
ISSUE_LINK = 'https://github.com/eclipse1482/recteq/issues'

DOMAIN = 'recteq'

PLATFORMS = ['climate', 'sensor']

GRILL_MODELS = {
    'RT590': {
        'DPS_POWER': '1',
        'DPS_TARGET': '101',
        'DPS_ACTUAL': '102',
        'DPS_PROBEA': '104',
        'DPS_PROBEB': '105',
        'TEMP_MIN': 200,
        'TEMP_MAX': 500,
        'LOW_MODE_TEMP': 180,  # Temperature for Low mode (e.g., Max Smoke)
        'FULL_MODE_TEMP': 600  # Temperature for Full mode
    },
    'RT700': {
        'DPS_POWER': '1',
        'DPS_TARGET': '101',
        'DPS_ACTUAL': '102',
        'DPS_PROBEA': '103',
        'DPS_PROBEB': '104',
        'TEMP_MIN': 200,
        'TEMP_MAX': 500,
        'LOW_MODE_TEMP': 180,  # Temperature for Low mode (e.g., Max Smoke)
        'FULL_MODE_TEMP': 600  # Temperature for Full mode
    }
}

GRILL_TYPES = list(GRILL_MODELS.keys())
CONF_GRILL_TYPE = 'grill_type'
DEFAULT_GRILL_TYPE = 'RT700'

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

DEFAULT_PROTOCOL = PROTOCOL_3_4

STR_INVALID_PREFIX = 'invalid_'
STR_PLEASE_CORRECT = 'please_correct'

FORCE_FAHRENHEIT = True