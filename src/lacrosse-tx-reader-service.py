#!/usr/bin/env python3

import json
import os
import sys
import datetime

print("INFO: INIT: lacrosse-tx-reader-service started ...")

CONFIGURATION_FILENAME = 'config.json'

API_BASE_URL_ENV_VAR_NAME = 'API_BASE_URL'
DEVICE_TOKEN_ENV_VAR_NAME = 'DEVICE_TOKEN'

API_BASE_URL_DEFAULT_VALUE = 'https://api.logreposit.com/v1/'


class JSONInputNotValidError(Exception):
    pass


def _read_configuration_file():
    with open(CONFIGURATION_FILENAME) as config_file:
        config = json.load(config_file)
        return config


def _read_configuration_file_and_build_mappings():
    config = _read_configuration_file()
    locations = config.get('locations')

    if not locations:
        print("WARN: No locations configured.")
        return {}

    mappings = {}

    for location in locations:
        if not location.get('deviceId') or not location.get('name'):
            continue

        mappings[location.get('deviceId')] = location.get('name')

    print("INFO: Parsed Location-Mappings: {}".format(mappings))

    return mappings


def _check_required_environment_variables():
    device_token = os.getenv(DEVICE_TOKEN_ENV_VAR_NAME, None)

    if device_token is None:
        print('Error: you have to specify a logreposit device-token in the env var \'{}\'!'
              .format(DEVICE_TOKEN_ENV_VAR_NAME))
        sys.exit(1)


def _validate_json_input(json_input):
    if not json_input.get('id'):
        print('ERROR: JSON Input did not have an `id` field.')
        raise JSONInputNotValidError()

    if not json_input.get('battery'):
        print('ERROR: JSON Input did not have a `battery` field.')
        # raise JSONInputNotValidError()

    if not json_input.get('newbattery'):
        print('ERROR: JSON Input did not have a `newbattery` field.')
        # raise JSONInputNotValidError()

    if not json_input.get('temperature_C'):
        print('ERROR: JSON Input did not have a `temperature_C` field.')
        # raise JSONInputNotValidError()

    if not json_input.get('mic'):
        print('ERROR: JSON Input did not have a `mic` field.')
        # raise JSONInputNotValidError


def _parse_line_and_publish_values(retrieved_line, api_base_url, device_token, mappings):
    parsed_line = json.loads(retrieved_line)

    if not parsed_line:
        print('ERROR: Could not parse line: Maybe no JSON? -> {}'.format(retrieved_line))
        raise JSONInputNotValidError()

    _validate_json_input(json_input=parsed_line)

    # TODO dom: just for debugging!
    with open('log.txt', 'a') as logfile:
        logfile.write(datetime.datetime.utcnow().isoformat() + ' -> ' + retrieved_line)

    device_id = parsed_line.get('id')
    location_name = mappings.get(device_id)

    if not location_name:
        print("WARN: UNKNOWN LOCATION FOR DEVICE: {}".format(retrieved_line))
        return

    print("INFO: TODO: Publish values for location '{}' to API with base-url '{}' for deviceId '{}': {}".format(
        location_name, api_base_url, device_token, retrieved_line))


def main():
    print("INFO: lacrosse-tx-reader-service started ...")

    _check_required_environment_variables()

    device_token = os.getenv(DEVICE_TOKEN_ENV_VAR_NAME)
    api_base_url = os.getenv(API_BASE_URL_ENV_VAR_NAME, API_BASE_URL_DEFAULT_VALUE)
    mappings = _read_configuration_file_and_build_mappings()

    while True:
        line = sys.stdin.readline()

        if not line:
            print('ERROR: No line received!')
            break

        try:
            _parse_line_and_publish_values(retrieved_line=line,
                                           api_base_url=api_base_url,
                                           device_token=device_token,
                                           mappings=mappings)
        except Exception as e:
            print('ERROR: Caught exception', e)


if __name__ == '__main__':
    main()
