"""
custom component to send notification if garage door is left open
"""

import datetime as dt
import functools
import logging

from homeassistant.const import STATE_ON, STATE_OFF, EVENT_TIME_CHANGED
import homeassistant.helpers.event as event
import homeassistant.util.dt as dt_util

# Create the logger
_LOGGER = logging.getLogger(__name__)

# HASS Requirements
DOMAIN = 'lighting_schedule'

# Dictionary for storing persistant variables across fuctions
PERSIST = {'mode': 'Dim', 'states': [0, 0, 0, 0, 0], 'last_cmd': None}
# States: [AUTOMATION_OFF, SUN_UP, KRISTEN_HOME, RYAN_HOME, FOYER_MOTION]
SCHEDULES = {'Dim': ((2, 3, 4, 5, 6, 7), 'switch.dim_scene'),
             'Bright': ((2, 3, 4, 5, 6, 7), 'switch.bright_scene'),
             'Movie': ((2, 3, 4, 5, 6, 7), 'switch.movie_scene'),
             'Night': ((3, 5, 7), 'switch.night_lights')}


def setup(hass, config):
    """ setup lighting schedule """
    event.async_track_state_change(
        hass, 'input_select.lighting_mode',
        functools.partial(_mode_changed, hass))
    event.async_track_state_change(
        hass, 'switch.automation_off',
        functools.partial(_autooff_changed, hass))
    event.async_track_state_change(
        hass, 'input_boolean.dark_outside',
        functools.partial(_sun_chaged, hass))
    event.async_track_state_change(
        hass, 'device_tracker.kristen_kristen',
        functools.partial(_kristenloc_changed, hass))
    event.async_track_state_change(
        hass, 'device_tracker.ryan_ryan',
        functools.partial(_ryanloc_changed, hass))
    event.async_track_state_change(
        hass, 'binary_sensor.foyer_motionsensor',
        functools.partial(_foyermot_changed, hass))
    event.async_track_state_change(
        hass, 'switch.all_on',
        functools.partial(_force_allon, hass),
        STATE_OFF, STATE_ON)
    event.async_track_state_change(
        hass, 'switch.all_off',
        functools.partial(_force_alloff, hass),
        STATE_OFF, STATE_ON)

    return True


def _mode_changed(hass, entity_id=None, old_state=None, new_state=None):
    """ lighting mode has changed """
    PERSIST['mode'] = str(new_state.state)
    PERSIST['last_cmd'] = None
    _eval_state(hass)


def _autooff_changed(hass, entity_id=None, old_state=None, new_state=None):
    """ automation off has changed """
    PERSIST['states'][0] = new_state.state == 'on'
    _eval_state(hass)


def _sun_chaged(hass, entity_id=None, old_state=None, new_state=None):
    """ dark_outside state has changed """
    PERSIST['states'][1] = new_state.state == 'off'
    _eval_state(hass)


def _kristenloc_changed(hass, entity_id=None, old_state=None, new_state=None):
    """ kristen's location has changed """
    PERSIST['states'][2] = new_state.state == 'home'
    _eval_state(hass)


def _ryanloc_changed(hass, entity_id=None, old_state=None, new_state=None):
    """ ryan's location has changed """
    PERSIST['states'][3] = new_state.state == 'home'
    _eval_state(hass)


def _foyermot_changed(hass, entity_id=None, old_state=None, new_state=None):
    """ foyer motion sensor has changed """
    PERSIST['states'][4] = new_state.state == 'on'
    _eval_state(hass)


def _force_allon(hass, entity_id=None, old_state=None, new_state=None):
    """ The All On button has been pressed """
    _call_service(hass, SCHEDULES[PERSIST['mode']][1], 'turn_on')
    _call_service(hass, 'switch.all_on', 'turn_off')


def _force_alloff(hass, entity_id=None, old_state=None, new_state=None):
    """ The All Off button has been pressed """
    _call_service(hass, SCHEDULES[PERSIST['mode']][1], 'turn_off')
    _call_service(hass, 'switch.all_off', 'turn_off')


def _eval_state(hass):
    """ determine proper action based on current state """
    state_str = ''.join(['1' if val else '0' for val in PERSIST['states']])
    state = int(state_str, 2)
    mode = PERSIST['mode']
    output = state in SCHEDULES[mode][0]
    _LOGGER.debug('Eval: %s %s = %s',
                  PERSIST['mode'], str(PERSIST['states']), repr(output))

    if output != PERSIST['last_cmd']:
        PERSIST['last_cmd'] = output
        if output:
            _call_service(hass, SCHEDULES[mode][1], 'turn_on')
        else:
            _call_service(hass, SCHEDULES[mode][1], 'turn_off')


def _call_service(hass, entity, service):
    """ set the state of an entity """
    _LOGGER.debug('Command: %s %s', entity, service)
    hass.services.call(
            'homeassistant', service, {'entity_id': entity})
