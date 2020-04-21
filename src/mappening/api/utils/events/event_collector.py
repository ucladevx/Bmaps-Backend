from mappening.utils.database import events_eventbrite_collection, events_current_processed_collection, events_facebook_processed_collection
from mappening.api.utils.eventbrite import eb_event_collector, eb_event_processor
from mappening.api.utils.facebook import fb_event_collector, fb_event_processor
from mappening.api.utils.events import event_processor

from flask import jsonify
import time, datetime, dateutil.parser, pytz
from dateutil.tz import tzlocal
import json
import re

from definitions import BASE_EVENT_START_BOUND

def get_month(month):
    try:
        month = int(month)
    except:
        return None

    if 1 <= month <= 12:
        return "{0:0=2d}".format(month)
    else:
        return None

class ListCursor(list):
    def __init__(self, l):
        self.l = l

    def __iter__(self):
        yield from self.l

    def count(self):
        return len(self.l)

def find_one(collection, find_dict):
    doc = collection.find_one(find_dict)
    res = ListCursor([])
    if doc:
        res = ListCursor([doc])
    return res

def collect_events_from(cursor, print_results=False, discard_no_loc_events=False):
    output = []
    if cursor.count() > 0:
        for event in cursor:
            if discard_no_loc_events and "location" not in event["place"]:
                continue
            output.append(event_processor.process_event_info(event))
            if print_results:
                # Python 2 sucks
                # event['name'] returns unicode string
                # to use with format(), another unicode string must be parent
                # unicode strings have 'u' in the front, as below
                # THEN: make sure Docker container locale / environment variable set, so print() itself works!!!!
                print(u'Event: {0}'.format(event.get('name', '<NONE>')))
    return output

def get_events_in_database(find_dict={}, one_result_expected=False, print_results=False):
    output = []
    # generator function that generates a collection.find() function that returns 
    # either a cursor or a list with a count function attached 
    # (to emulate a cursor in the case of only one result being expected)
    gen_find = lambda events_collection : lambda find_dict : find_one(events_collection, find_dict) if one_result_expected else events_collection.find(find_dict)

    find_in_eventbrite = gen_find(events_current_processed_collection)
    find_in_facebook = gen_find(events_facebook_processed_collection)

    eventbrite_events_cursor = find_in_eventbrite(find_dict)
    facebook_events_cursor = find_in_facebook(find_dict)

    if eventbrite_events_cursor.count() <= 0 and facebook_events_cursor.count() <= 0:
        print('No events found with attributes:' + str(find_dict))
        return []

    output += collect_events_from(eventbrite_events_cursor)
    if not one_result_expected or len(output) <= 0:
        output += collect_events_from(facebook_events_cursor, print_results, True)

    return output
    

def find_events_in_database(find_dict={}, one_result_expected=False, print_results=False):
    output = get_events_in_database(find_dict, one_result_expected, print_results)
    return jsonify({'features': output, 'type': 'FeatureCollection'})

# Get all UCLA-related events from sources (Eventbrite, FB, etc.) and add to database
def update_ucla_events_database(use_test=False, days_back_in_time=0, clear_old_db=False):
    event_processor.clean_up_existing_events(days_back_in_time)

    # Eventbrite events
    events = eb_event_collector.get_raw_events(days_back_in_time)
    eb_event_collector.update_database(events)
    eb_count = eb_event_processor.process_events(events)

    # Facebook Events
    # TODO
    fb_events = fb_event_collector.get_interested_events(days_back_in_time)
    # fb_event_collector.update_database(events)
    fb_count = len(fb_event_processor.process_events(fb_events))

    # processed_db_events 'todo'
    new_events_data = {'metadata': {'events': eb_count + fb_count}}
    new_count = eb_count + fb_count

    return 'Updated with {0} retrieved events, {1} new ones.'.format(new_events_data['metadata']['events'], new_count)
