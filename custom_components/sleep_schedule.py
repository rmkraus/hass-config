"""
custom component to have the house react to people sleeping.
"""

import functools
import logging

import homeassistant.helpers.event as event

# Create the logger
_LOGGER = logging.getLogger(__name__)

# HASS Requirements
DOMAIN = 'sleep_schedule'


def setup(hass, config):
    """ setup lighting schedule """
    event.async_track_state_change(
        hass, 'sensor.everyone_is_awake',
        functools.partial(_everyone_is_awake, hass))
    event.async_track_state_change(
        hass, 'sensor.parents_sleeping',
        functools.partial(_parents_sleeping, hass))

    return True


def _everyone_is_awake(hass, entity_id=None, old_state=None, new_state=None):
    """ The status of 'everyone is awake' has changed. """
    _LOGGER.debug('%s is now %s', entity_id, repr(new_state.state))
    if new_state.state in [False, 'False', 'unknown']:
        return

    _call_service(hass, 'input_select.lighting_mode', \
                  'input_select', 'select_option', \
                  {"option": "Dim"})


def _parents_sleeping(hass, entity_id=None, old_state=None, new_state=None):
    """ The status of 'parents sleeping' has changed. """
    _LOGGER.debug('%s is now %s', entity_id, repr(new_state.state))
    if new_state.state in [False, 'False', 'unknown']:
        return

    _call_service(hass, 'input_select.lighting_mode', \
                  'input_select', 'select_option', \
                  {"option": "Night"})
    _call_service(hass, 'vacuum.roomba', \
                  'homeassistant', 'turn_on')

    tv_state = _get_state(hass, 'media_player.living_room_universal')
    _LOGGER.debug('The living room TV is currently %s', repr(tv_state))
    if tv_state != 'off':
        _call_service(hass, 'media_player.living_room_universal', \
                      'homeassistant', 'turn_off')


def _call_service(hass, entity, domain, service, data=None):
    """ set the state of an entity """
    _LOGGER.debug('Command: %s %s', entity, service)

    data = data or {}
    data.update({'entity_id': entity})

    hass.services.call(domain, service, data)


def _get_state(hass, entity):
    """ get the state of an entity """
    _LOGGER.debug('Getting state for %s', entity)
    return hass.states.get(entity).state
