from mappening.utils.database import events_facebook_processed_collection
from mappening.utils.secrets import FACEBOOK_USER_ACCESS_TOKEN
from mappening.ml.autocategorization import categorizeEvents
from mappening.ml.autofood import labelFreeFood

import os
import sys
import requests
import json
import time, datetime, dateutil.parser, pytz
from dateutil.tz import tzlocal
from pprint import pprint
from tqdm import tqdm   # a progress bar, pretty

from definitions import API_UTILS_PATH

# need this to run file locally, or else won't know where to find mappening.utils.*
sys.path.insert(0, './../../..')

# Specify version in case most updated version (default if not specified) removes functionality, causing errors
API_VERSION_STR = 'v5.0/'
BASE_URL = 'https://graph.facebook.com/' + API_VERSION_STR

# Get events by adding page ID and events field
BASE_EVENT_URL = BASE_URL

# Id is ALWAYS returned, for any field, explicitly requested or not, as long as there is data
EVENT_FIELDS = ['name', 'category', 'place', 'description', 'start_time', 'end_time', 'event_times',
                'attending_count', 'maybe_count', 'interested_count', 'noreply_count', 'is_canceled',
                'ticket_uri', 'cover']


# def format_time(time):
#     # %z gets time zone difference in +/-HHMM from UTC
#     return time.strftime('%Y-%m-%d %H:%M:%S %z')

# def entity_in_right_location(loc_data):
#     """
#     if zip code, check in UCLA zip codes (first 5 digits)
#     if no zip code, check that in Los Angeles, CA
#     """
#     if 'zip' in loc_data:
#         zip_string = loc_data['zip'][:5]
#         if zip_string in UCLA_ZIP_STRINGS:
#             return True
#     elif 'city' in loc_data and 'state' in loc_data:
#         if loc_data['city'] == 'Los Angeles' and loc_data['state'] == 'CA':
#             return True
#     return False

# def general_search_results(search_term, search_args):
#     """
#     Generate general search results
#     """
#     current_entities = {}
#     search_args['q'] = search_term
#     resp = s.get(SEARCH_URL, params=search_args)
#     if resp.status_code != 200:
#         print(
#             'Error searching for {0}s with term {1}! Status code {2}: {3}'
#             .format(search_args.get('type', 'page'), search_term, resp.status_code, resp.json().get('error', 'No error message'))
#         )
#         return {}
#     elif 'data' not in resp.json():
#         print('{0} search results missing data field!'.format(search_args.get('type', 'page')))
#         return {}

#     for entity in resp.json()['data']:
#         # filter out pages definitely not near UCLA
#         # if no location, must keep for now, else check its location
#         if 'location' not in entity or entity_in_right_location(entity['location']):
#             current_entities[entity['id']] = entity['name']
#     return current_entities

# def process_event(event, host_info, add_duplicate_tag=False):
#     """
#     takes in event dict ({many attributes: values}), returns dict of event dicts from event id to all info
#     passes in other data for manually added fields (NOT from FB, but for our own purposes)
#     """
#     app_access_token = get_app_token()

#     # URL parameters for refreshing / updating events info, including subevents
#     sub_event_call_args = {
#         'fields': ','.join(EVENT_FIELDS),
#         'access_token': app_access_token
#     }

#     # only want events with the specified accepted location within UCLA
#     if 'place' not in event:
#         return {}
#     event_place_info = event['place']
#     if 'location' not in event_place_info and 'name' in event_place_info:
#         # many places have location in name only
#         # TODO: get these out with ML

#         # temp code to gather all place names from events we find
#         # no repeats 
#         # if unknown_locations_collection.find_one({'location_name': event_place_info['name']}):
#         #     return {}

#         # unknown_loc_dict = {
#         #     'event_id': event['id'],
#         #     'event_name': event['name'],
#         #     'location_name': event_place_info['name']
#         # }
#         # unknown_locations_collection.insert_one(unknown_loc_dict)
#         return {}
        
#     if not entity_in_right_location(event_place_info['location']):
#         return {}

#     # for when updating old events and transferring manually added tags over
#     if add_duplicate_tag:
#         event['duplicate_occurrence'] = True

#     expanded_event_dict = {}
#     # check for multi-day events, need API call again
#     if 'event_times' in event:
#         # need to call API again for event fields
#         # batch call with multiple IDs: slightly faster from less network traffic, Facebook's end
#         sub_ids = []
#         for sub_event_header in event['event_times']:
#             sub_ids.append(sub_event_header['id'])
#         sub_event_call_args['ids'] = ','.join(sub_ids)

#         resp = s.get(BASE_EVENT_URL, params=sub_event_call_args)
#         # print(resp.url)
#         if resp.status_code != 200:
#             print(
#                 'Error trying to retrieve sub-event data of event {0}: Status code {1}'
#                 .format(event['id'], resp.status_code)
#             )
#             # just skip this multi-day event if sub-events not successfully retrieved
#             return {}
#         expanded_event_dict = resp.json()
#         # add special "duplicate_occurrence" tag for event occurrences in the future that
#         # won't be searchable, because the 1st event start time has passed already
#         # don't need to refresh for the 1st event, since that matches the total event start time
#         for sub_event in expanded_event_dict.values():
#             # using dict.values() and editing each item in list still changes original dictionary
#             if sub_event['start_time'] != event['start_time']:
#                 sub_event['duplicate_occurrence'] = True
#     else:
#         expanded_event_dict.update({event['id']: event})

#     # final cleaning of all event instances, including repeated occurrences
#     for event_occurrence in expanded_event_dict.values():
#         # clean the category attribute if needed
#         if 'category' in event_occurrence:
#             if event_occurrence['category'].startswith('EVENT_'):
#                 event_occurrence['category'] = event_occurrence['category'][6:]
#             elif event_occurrence['category'].endswith('_EVENT'):
#                 event_occurrence['category'] = event_occurrence['category'][:-6]
#         # save from which page / group this event was found
#         event_occurrence['hoster'] = host_info

#         # for debugging: save when each event was updated, in LA time
#         current_time = datetime.datetime.now(tzlocal()).astimezone(pytz.timezone('America/Los_Angeles'))
#         # get up to microseconds with %f, probably not needed but just in case
#         event_occurrence['time_updated'] = current_time.strftime('%Y-%m-%d %H:%M:%S.%f')
#     return expanded_event_dict

s = requests.Session()

app_access_token = "EAAFB1Et4EnkBAA7U1Wdhz90TdbU3UTkFOWz1iaNo0ZBB3BawALuyFxKpB1SEZBeZBrQtRbUr4NCgwnZBAgmuQgZCJkSZBxZAReBo8yNZBhsFmGJrpWQpBSdJB4uQr4pE2F0PV5IeQvfjH7jy5h478lhqTcYhBCJMGnzZCGqFILcAxIQZDZD"
# Process for frontend to use it 
def process_events(all_events):

    filtered_events = []

    for event in all_events:

        # some events don't have a place, if they don't maybe just remove them for now and later try to get the place
        # TODO: find place from owner's location if place is not present
        if "place" not in event:
            # don't add to filtered_events
            continue

        # some events have "place" but no "place.location"
        # this happens with some events that are imported to facebook from eventbrite
        # I.E. they have "owner" == Eventbrite
        # if this happens we can just exclude them from the facebook database collection
        # this might even be a good thing because if they are eventbrite events, it would be difficult to dedupe across collections anyways
        if "location" not in event["place"]:
            continue

        # change "zip" of place.location to "zipcode"
        if 'location' in event['place'] and 'zip' in event['place']['location']:
            event['place']['location']['zipcode'] = event['place']['location'].pop('zip')
        
        # if event does not have an endtime, give it an endtime 1 hour into the future
        if "end_time" not in event:
            event["end_time"] = (datetime.datetime.strptime(event["start_time"], '%Y-%m-%dT%H:%M:%S%z') + datetime.timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S%z')
            print(event["end_time"])


        filtered_events.append(event)

    # URL parameters for refreshing / updating events info, including subevents
    sub_event_call_args = {
        'fields': ','.join(EVENT_FIELDS),
        'access_token': app_access_token
    }

    additional_events = []
    # check for multiday events
    for event in all_events:
        expanded_event_dict = {}
        # check for multi-day events, need API call again
        if 'event_times' in event:
            # need to call API again for event fields
            # batch call with multiple IDs: slightly faster from less network traffic, Facebook's end
            sub_ids = []
            for sub_event_header in event['event_times']:
                sub_ids.append(sub_event_header['id'])
            # sub_event_call_args['ids'] = ','.join(sub_ids)

            for id in sub_ids:
                
                resp = s.get(BASE_EVENT_URL + id, params=sub_event_call_args)
                # print(resp.url)
                if resp.status_code != 200:
                    print(
                        'Error trying to retrieve sub-event data of event {0}: Status code {1}'
                        .format(event['id'], resp.status_code)
                    )
                    # just skip this multi-day event if sub-events not successfully retrieved
                    continue
                
                expanded_event_dict = resp.json()

                # not sure if this is needed --haki
                # # add special "duplicate_occurrence" tag for event occurrences in the future that
                # # won't be searchable, because the 1st event start time has passed already
                # # don't need to refresh for the 1st event, since that matches the total event start time
                # for sub_event in expanded_event_dict.values():
                #     # using dict.values() and editing each item in list still changes original dictionary
                #     if sub_event['start_time'] != event['start_time']:
                #         sub_event['duplicate_occurrence'] = True

                additional_events.append(expanded_event_dict)
        # I have no idea what this else statement is doing --haki
        # else:
        #     expanded_event_dict.update({event['id']: event})


    print("additional events")
    print(len(additional_events))

    filtered_events.extend(additional_events)

    # need to map facebook categories to bmaps categories
    # also do we need to run the ML for figuring out the categories?
    categorized_clean_events = categorizeEvents(filtered_events)
    categorized_clean_events = labelFreeFood(categorized_clean_events)
        
    # Autocategorization has a cleaner way to do this path switching
    savedPath = os.getcwd()
    os.chdir(API_UTILS_PATH)
    with open('facebk.json', 'w') as f:
        json.dump(categorized_clean_events, f, sort_keys=True, indent=4, separators=(',', ': '))
    os.chdir(savedPath)

    # add filtered events to database
    events_facebook_processed_collection.delete_many({})
    events_facebook_processed_collection.insert_many(categorized_clean_events)

    return categorized_clean_events
        
