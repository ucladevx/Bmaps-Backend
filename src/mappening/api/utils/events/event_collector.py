from mappening.utils.database import events_fb_collection, events_eventbrite_collection, events_test_collection, events_current_processed_collection
from mappening.api.utils.eventbrite import eb_event_collector, eb_event_processor
from mappening.api.utils.facebook2 import fb2_event_collector
from mappening.api.utils.events import event_processor 

from flask import jsonify
import time, datetime, dateutil.parser, pytz
from dateutil.tz import tzlocal
import json
import re

from definitions import BASE_EVENT_START_BOUND

# each website source has its own database, where raw event info is stored
all_raw_collections = {
    'eventbrite': events_eventbrite_collection,
    'facebook': events_fb_collection,
    'test': events_test_collection
}

def get_month(month):
    try:
        month = int(month)
    except:
        return None
        
    if 1 <= month <= 12:
        return "{0:0=2d}".format(month)
    else:
        return None

def get_events_in_database(find_dict={}, one_result_expected=False, print_results=False):
    output = []

    if one_result_expected:
        single_event = events_current_processed_collection.find_one(find_dict)
        if single_event:
            output.append(event_processor.process_event_info(single_event))
            if print_results:
                print(u'Event: {0}'.format(single_event.get('name', '<NONE>')))
        else:
            # careful: output is still empty here; make sure output list never set ANYWHERE else
            # i.e. no other conditional branch is entered after this one, same with multiple event case below
            print('No single event with attributes:' + str(find_dict))
    else:
        events_cursor = events_current_processed_collection.find(find_dict)
        if events_cursor.count() > 0:
            for event in events_cursor:
                output.append(event_processor.process_event_info(event))
                if print_results:
                    # Python 2 sucks
                    # event['name'] returns unicode string
                    # to use with format(), another unicode string must be parent
                    # unicode strings have 'u' in the front, as below
                    # THEN: make sure Docker container locale / environment variable set, so print() itself works!!!!
                    print(u'Event: {0}'.format(event.get('name', '<NONE>')))
        else:
            print('No events found with attributes:' + str(find_dict))

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

    # processed_db_events 'todo'
    new_events_data = {'metadata': {'events': eb_count}}
    new_count = eb_count
   
    return 'Updated with {0} retrieved events, {1} new ones.'.format(new_events_data['metadata']['events'], new_count)
