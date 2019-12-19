#!/usr/bin/env python3

import datetime
import json
import os
import requests
import sys
import threading
import time
import traceback


CONFIGURATION_FILENAME = 'config.json'
API_BASE_URL_ENV_VAR_NAME = 'API_BASE_URL'
DEVICE_TOKEN_ENV_VAR_NAME = 'DEVICE_TOKEN'
UPDATE_INTERVAL_IN_SECONDS_ENV_VAR_NAME = 'UPDATE_INTERVAL'
API_BASE_URL_DEFAULT_VALUE = 'https://api.logreposit.com/v1/'


class JSONInputNotValidError(Exception):
    pass


reading_collection = {}


def _log(level, message):
    log_prefix = datetime.datetime.utcnow().isoformat()
    msg = '{} -> {}: {}'.format(log_prefix, level, message)
    print(msg)


def _read_configuration_file():
    with open(CONFIGURATION_FILENAME) as config_file:
        config = json.load(config_file)
        return config


def _read_configuration_file_and_build_mappings():
    config = _read_configuration_file()
    locations = config.get('locations')

    if not locations:
        _log(level='WARN', message='No locations configured.')
        return {}

    mappings = {}

    for location in locations:
        if not location.get('deviceId') or not location.get('name'):
            continue

        mappings[location.get('deviceId')] = location.get('name')

    _log(level='INFO', message='Parsed Location-Mappings: {}'.format(mappings))

    return mappings


def _check_required_environment_variables():
    device_token = os.getenv(DEVICE_TOKEN_ENV_VAR_NAME, None)

    if device_token is None:
        _log(
            level='ERROR',
            message='Error: you have to specify a logreposit device-token in the env var \'{}\'!'.format(
                DEVICE_TOKEN_ENV_VAR_NAME)
        )
        sys.exit(1)


def _validate_json_input(json_input):
    if json_input.get('time') is None:
        _log(level='ERROR', message='JSON Input did not have an `time` field.')
        raise JSONInputNotValidError()

    if json_input.get('id') is None:
        _log(level='ERROR', message='JSON Input did not have an `id` field.')
        raise JSONInputNotValidError()

    if json_input.get('battery') is None:
        _log(level='ERROR', message='JSON Input did not have a `battery` field.')
        raise JSONInputNotValidError()

    if json_input.get('newbattery') is None:
        _log(level='ERROR', message='JSON Input did not have a `newbattery` field.')
        raise JSONInputNotValidError()

    if json_input.get('model') is None:
        _log(level='ERROR', message='JSON Input did hot have a `model` field.')
        raise JSONInputNotValidError()


def _parse_date(date_from_rtl433):
    # Input format: 2018-08-14 17:10:20
    date = datetime.datetime.strptime(date_from_rtl433, '%Y-%m-%d %H:%M:%S')
    timestamp = date.replace(tzinfo=datetime.timezone.utc).isoformat()
    return timestamp


def _convert_to_reading(retrieved_line, location_mappings):
    parsed_line = json.loads(retrieved_line)

    if not parsed_line:
        _log(level='ERROR', message='Could not parse line: Maybe no JSON? -> {}'.format(retrieved_line))
        raise JSONInputNotValidError()

    _validate_json_input(parsed_line)

    date = parsed_line.get('time')
    device_id = parsed_line.get('id')
    device_model = parsed_line.get('model')
    battery = parsed_line.get('battery')
    new_battery = parsed_line.get('newbattery')
    temperature = parsed_line.get('temperature_C')
    humidity = parsed_line.get('humidity')

    location = location_mappings.get(device_id)

    reading_new_battery = None
    if new_battery is not None:
        if new_battery:
            reading_new_battery = True
        else:
            reading_new_battery = False

    reading_battery_ok = None
    if battery is not None:
        if battery == 'OK':
            reading_battery_ok = True
        else:
            reading_battery_ok = False

    iso_date = _parse_date(date_from_rtl433=date)

    reading = {
        'date': iso_date,
        'location': location,
        'sensorId': device_id,
        'sensorModel': device_model,
        'batteryNew': reading_new_battery,
        'batteryOk': reading_battery_ok,
        'temperature': temperature,
        'humidity': humidity
    }

    return reading


def _build_request_data(reading):
    data = {
        'deviceType': 'LACROSSE_TECHNOLOGY_TX',
        'data': reading
    }
    return data


def _publish_values(api_base_url, device_token, reading):
    _log(
        level='INFO',
        message="Publishing values to API with base-url '{}': {}".format(api_base_url, json.dumps(reading))
    )

    url = api_base_url + 'ingress'
    headers = {
        'x-device-token': device_token
    }
    request_data = _build_request_data(reading=reading)

    print('Publishing values to {}: {}'.format(url, json.dumps(request_data)))
    response = requests.post(url, json=request_data, headers=headers)

    if response.status_code != 202:
        print('ERROR: Got HTTP status code \'{}\': {}'.format(response.status_code, response.text))
    else:
        print('Successfully published data.')


def _parse_line_and_publish_values(retrieved_line, api_base_url, device_token, mappings, update_interval):
    reading = _convert_to_reading(retrieved_line=retrieved_line, location_mappings=mappings)

    location_name = reading.get('location')

    if not location_name:
        _log(level='WARN', message='UNKNOWN LOCATION FOR DEVICE \'{}\': {}'.format(reading.get('id'), retrieved_line))
        return

    if update_interval is None:
        _publish_values(api_base_url=api_base_url, device_token=device_token, reading=reading)
    else:
        _log(level='INFO',
             message='adding reading of sensor at location \'{}\' to the collection'.format(location_name))
        reading_collection[location_name] = reading


def _publish_async(api_base_url, device_token, sleep_time):
    while True:
        try:
            time.sleep(sleep_time)

            collection_copy = json.loads(json.dumps(reading_collection))
            reading_collection.clear()

            for location, reading in collection_copy.items():
                _publish_values(api_base_url=api_base_url, device_token=device_token, reading=reading)
        except:
            msg = traceback.format_exc()
            _log(level='ERROR', message='Caught exception in _publish_async: {}'.format(msg))


def main():
    _log(level='INFO', message='lacrosse-tx-reader-service started ...')

    _check_required_environment_variables()

    device_token = os.getenv(DEVICE_TOKEN_ENV_VAR_NAME)
    api_base_url = os.getenv(API_BASE_URL_ENV_VAR_NAME, API_BASE_URL_DEFAULT_VALUE)
    update_interval_str = os.getenv(UPDATE_INTERVAL_IN_SECONDS_ENV_VAR_NAME)
    mappings = _read_configuration_file_and_build_mappings()

    update_interval = None

    if update_interval_str is not None:
        update_interval = int(update_interval_str)
        thread = threading.Thread(target=_publish_async,
                                  args=(api_base_url, device_token, update_interval),
                                  daemon=True)
        thread.start()

    while True:
        line = sys.stdin.readline()

        if not line:
            _log(level='ERROR', message='No line received!')
            break

        try:
            _parse_line_and_publish_values(retrieved_line=line,
                                           api_base_url=api_base_url,
                                           device_token=device_token,
                                           mappings=mappings,
                                           update_interval=update_interval)
        except:
            msg = traceback.format_exc()
            _log(level='ERROR', message='Caught exception: {}'.format(msg))


if __name__ == '__main__':
    main()
