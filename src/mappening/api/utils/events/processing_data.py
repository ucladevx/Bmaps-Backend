from flask import jsonify
import time, datetime, dateutil.parser, pytz
from dateutil.tz import tzlocal
from tqdm import tqdm   # a progress bar, pretty
import json
import os
import re

from definitions import CENTER_LATITUDE, CENTER_LONGITUDE, BASE_EVENT_START_BOUND

from mappening.utils.database import events_fb_collection, events_eventbrite_collection, events_test_collection, fb_pages_saved_collection
from mappening.utils.database import events_current_processed_collection

from mappening.api.utils.facebook_scraper import get_data, process_data 

from mappening.api.utils.eventbrite_scraper import eventbrite_scraper

# each website source has its own database, where raw event info is stored
all_raw_collections = {
    'eventbrite': events_eventbrite_collection,
    'facebook': events_fb_collection,
    'test': events_test_collection
}
#Processing events 

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