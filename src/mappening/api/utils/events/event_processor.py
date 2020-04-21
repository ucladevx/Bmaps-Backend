from mappening.utils.database import events_fb_collection, events_eventbrite_collection, events_current_processed_collection, events_internal_added_collection

from flask import jsonify
import time, datetime, dateutil.parser, pytz
from dateutil.tz import tzlocal
from tqdm import tqdm   # a progress bar, pretty
import json
import os
import re

from definitions import CENTER_LATITUDE, CENTER_LONGITUDE, BASE_EVENT_START_BOUND

def process_event_info(event):
    """
        :Description: Returns GeoJSON of singular event matching event name

        :param str event_name: case-insensitive name string to search database for exact match
    """
    # Remove certain keys from dictionary
    event.pop('_id', None) # pop is basically get and remove; pop(key, default)
    event.get('place', {}).pop('id', None) # pop is basically used as if it exists, remove it
    eId = event.pop('id')

    # Clean up certain entries
    event['stats'] = {
        'attending': event.pop('attending_count', 0),
        'noreply': event.pop('noreply_count', 0),
        'interested': event.pop('interested_count', 0),
        'maybe': event.pop('maybe_count', 0)
    }
    if 'source' in event.get('cover', {}): #default of get `{}` so `in` works
        cover_picture = event.pop('cover')['source']
        event['cover_picture'] = cover_picture
    if 'name' in event.get('hoster', {}):
        host = event.pop('hoster')['name']
        event['hoster'] = host

    # Create GeoJSON

    # TODO: Check if coordinates are outside UCLA
    formatted_info = {
        # will ALWAYS have an ID
        'id': eId,
        'type': 'Feature',
        'geometry': {
            # no coordinates? default to Bruin Bear
            'coordinates': [
                event['place']['location'].get('longitude', float(CENTER_LONGITUDE)),
                event['place']['location'].get('latitude', float(CENTER_LATITUDE))
            ],
            'type': 'Point'
        },
        'properties': event
    }

    return formatted_info

def processed_time(old_time_str):
    # if not valid time string, return default value from dict.get()
    try:
        # use dateutil parser to get time zone
        time_obj = dateutil.parser.parse(old_time_str)
    except ValueError:
        return old_time_str
    # Formatting according to date.parse() requirements
    # time zone offset always off of GMT
    res_time_str = datetime.datetime.strftime(time_obj, '%a, %d %b %Y %H:%M:%S GMT%z')
    return res_time_str

def construct_date_regex(raw_date):
    if not raw_date:
        return None

    # Try to parse date
    try:
        # Use dateutil parser to get time zone
        time_obj = dateutil.parser.parse(raw_date)
    except ValueError:
        # Got invalid date string
        print('Invalid date string, cannot be parsed!')
        return None

    # Get the date string by YYYY-MM-DD format
    time_str = datetime.datetime.strftime(time_obj, '%Y-%m-%d')

    date_regex_str = '^{0}.*'.format(time_str)
    date_regex_obj = re.compile(date_regex_str)
    return date_regex_obj

def time_in_past(time_str, days_before=BASE_EVENT_START_BOUND):
    """
    takes in an FB formatted timestamp: Y-m-d'T'H:M:S<tz>
    to account for weird timezone things, construct 2 datetime objects
    one from simply parsing the string, and another from current time
    required by Python (and to standardize), need to convert both times to UTC explicitly, use pytz module
    return boolean, if given time string has passed in real time
    """
    try:
        # Use dateutil parser to get time zone
        time_obj = dateutil.parser.parse(time_str).astimezone(pytz.UTC)
    except ValueError:
        # Got invalid date string
        print('Invalid datetime string from event \'start_time\' key, cannot be parsed!')
        return False
    # need to explicitly set time zone (tzlocal() here), or else astimezone() will not work
    now = datetime.datetime.now(tzlocal()).astimezone(pytz.UTC)

    # if time from string is smaller than now, with offset (to match time range of new events found)
    # offset shifts the boundary back in time, for which events to update rather than delete
    return time_obj <= now - datetime.timedelta(days=days_before)
    
# If needed, clean database of duplicate documents
def remove_db_duplicates(changed_collection):
    """
    simply save each unique document and delete any that have been found already
    """
    # a set, not a dict
    unique_ids = set()
    dups = []
    # IMPORTANT: do not take down _id, jsonify can't handle type
    for item in collection.find({}, {'_id': False}):
        # assume all items must have a unique id key-value pair
        curr_id = item['id']
        if curr_id in unique_ids:
            dups.append(item)
            collection.delete_many({'id': curr_id})
        else:
            unique_ids.add(curr_id)

    print('Removed {0} duplicates.'.format(len(dups)))
    return dups

# ONLY clean up processed events, never raw DB
def clean_up_existing_events(days_before=BASE_EVENT_START_BOUND):
    """
    update events currently in processed events database before new ones put in
    means remove ones too old and re-search the rest
    events = list of all event info dicts
    """
    print('Go through currently stored events to update.')
    kept_events = {}
    for processed_event in tqdm(events_current_processed_collection.find()):
        # for multi-day events that were found a long time ago, have to recall API to check for updates (e.g. cancelled)
        # to tell if multi-day event, check "duplicate_occurrence" tag
        
        if not time_in_past(processed_event['start_time'], days_before):
            # TODO: make a general process_event function for events of each source
            # this line is FB specific
            # updated_event_dict = process_event(event, event.get('hoster', '<NONE>'), event.get('duplicate_occurrence', False))
            kept_events.update(processed_event)
        # return a dict of kept event IDs to their info
    return kept_events
