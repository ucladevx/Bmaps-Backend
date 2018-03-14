from mappening.utils.database import saved_pages_collection, unknown_locations_collection, events_ml_collection
from mappening.utils.secrets import FACEBOOK_USER_ACCESS_TOKEN

import requests
import json
import time, datetime, dateutil.parser, pytz
from dateutil.tz import tzlocal
from pprint import pprint
from tqdm import tqdm   # a progress bar, pretty

# for sys.exit()
import sys
import os

# Specify version in case most updated version (default if not specified) removes functionality, causing errors
API_VERSION_STR = 'v2.10/'
BASE_URL = 'https://graph.facebook.com/' + API_VERSION_STR

# Got APP_ID and APP_SECRET from Mappening app with developers.facebook.com
ACCESS_TOKEN_URL = BASE_URL + 'oauth/access_token'

SEARCH_URL = BASE_URL + 'search'

# Updated coordinates of Bruin Bear
CENTER_LATITUDE = 34.070966
CENTER_LONGITUDE = -118.445
SEARCH_TERMS = ['ucla', 'bruin', 'ucla theta', 'ucla kappa', 'ucla beta']
UCLA_ZIP_STRINGS = ['90024', '90095']

# Get events by adding page ID and events field
BASE_EVENT_URL = BASE_URL

# Id is ALWAYS returned, for any field, explicitly requested or not, as long as there is data
EVENT_FIELDS = ['name', 'category', 'place', 'description', 'start_time', 'end_time', 'event_times',
                'attending_count', 'maybe_count', 'interested_count', 'noreply_count', 'is_canceled',
                'ticket_uri', 'cover']

# the time period before now, IN DAYS, for finding and updating events instead of removing them 
BASE_EVENT_START_BOUND = 0

s = requests.Session()

def format_time(time):
    # %z gets time zone difference in +/-HHMM from UTC
    return time.strftime('%Y-%m-%d %H:%M:%S %z')

def get_event_time_bounds(days_before):
    # back_jump = 60        # for repeating events that started a long time ago
    back_jump = days_before # arbitrarily allow events that start 1 day ago (allows refresh to keep current day's events)
    forward_jump = 60       # and 60 days into the future
    now = datetime.datetime.now()
    before_time = now - datetime.timedelta(days=back_jump)
    after_time = now + datetime.timedelta(days=forward_jump)
    return (format_time(before_time), format_time(after_time))

def get_app_token():
    # token_args = {
    #     'client_id': FACEBOOK_APP_ID,
    #     'client_secret': FACEBOOK_APP_SECRET,
    #     'grant_type': 'client_credentials'
    # }
    # resp = s.get(ACCESS_TOKEN_URL, params=token_args)
    # if resp.status_code != 200:
    #     print('Error in getting access code! Status code {}'.format(resp.status_code))
    #     return ''
    # return resp.json()['access_token']

    # don't use app access token for now, not allowed to search groups
    # but this needs to update every 60 days!
    return FACEBOOK_USER_ACCESS_TOKEN


def entity_in_right_location(loc_data):
    """
    if zip code, check in UCLA zip codes (first 5 digits)
    if no zip code, check that in Los Angeles, CA
    """
    if 'zip' in loc_data:
        zip_string = loc_data['zip'][:5]
        if zip_string in UCLA_ZIP_STRINGS:
            return True
    elif 'city' in loc_data and 'state' in loc_data:
        if loc_data['city'] == 'Los Angeles' and loc_data['state'] == 'CA':
            return True
    return False

def general_search_results(search_term, search_args):
    """
    Generate general search results
    """
    current_entities = {}
    search_args['q'] = search_term
    resp = s.get(SEARCH_URL, params=search_args)
    if resp.status_code != 200:
        print(
            'Error searching for {0}s with term {1}! Status code {2}: {3}'
            .format(search_args.get('type', 'page'), search_term, resp.status_code, resp.json().get('error', 'No error message'))
        )
        return {}
    elif 'data' not in resp.json():
        print('{0} search results missing data field!'.format(search_args.get('type', 'page')))
        return {}

    for entity in resp.json()['data']:
        # filter out pages definitely not near UCLA
        # if no location, must keep for now, else check its location
        if 'location' not in entity or entity_in_right_location(entity['location']):
            current_entities[entity['id']] = entity['name']
    return current_entities

def find_ucla_entities():
    """
    for searching all types: place, page, and group
    """
    app_access_token = get_app_token()
    ucla_entities = {}
    # args for pages
    page_search_args = {
        'type': 'page',
        'limit': '500',     # limit is as high as desired, but these searches top out at ~350 entries now
        'fields': 'name,location',
        'access_token': app_access_token
    }
    # group search args
    group_search_args = {
        'type': 'group',
        'limit': '1000',    # returns about 550 groups, from last check
        'fields': 'name',   # groups do not have location
        'access_token': app_access_token
    }

    for term in SEARCH_TERMS:
        ucla_entities.update(general_search_results(term, page_search_args))
        ucla_entities.update(general_search_results(term, group_search_args))

    # don't need a query string for this, still need to filter out by location
    place_search_args = {
        'type': 'place',
        'center': str(CENTER_LATITUDE) + ',' + str(CENTER_LONGITUDE),
        'distance': '1000',
        'limit': '100',
        'fields': 'name,location',
        'access_token': app_access_token
    }
    # multiple result pages probably needed, since limit here per page is maxed at 100
    # but don't keep calling API or else rate limiting might apply, and farther results = less relevant
    # will break out manually if no next page
    page_num = 0
    curr_url = SEARCH_URL
    while page_num < 5:
        resp = s.get(curr_url, params=place_search_args)
        if resp.status_code != 200:
            print(
                'Error searching for places, on results page {0}! Status code {1}'
                .format(page_num, resp.status_code)
            )
            break
        responses = resp.json()
        if 'data' not in responses:
            print('Missing data field from place search results!')
            break

        for place in responses['data']:
            # skip place pages already added, immediately
            # every place should have location data, but just in case, ignore ones that don't
            if place['id'] in ucla_entities or 'location' not in place:
                continue
            elif entity_in_right_location(place['location']):
                ucla_entities[place['id']] = place['name']
        
        # check if there is a next page of results
        if 'paging' not in responses or 'next' not in responses['paging']:
            break
        else:
            curr_url = responses['paging']['next']
        page_num += 1

    # a dictionary, to keep only unique pages
    return ucla_entities

# json file expected to be a bunch of dicts, each for 1 page, with page_id and name
# one time usage, basically
def add_pages_from_json(filename):
    page_list = []
    with open(filename) as infile:
        for line in tqdm(infile):
            # takes each line as a dict and from each, takes out only 2 key-values, id and name
            abridged_info = {k: json.loads(line).get(k, None) for k in ('page_id', 'name')}
            # change key name to id
            abridged_info['id'] = abridged_info.pop('page_id')
            page_list.append(abridged_info)

    for page in tqdm(page_list):
        if saved_pages_collection.find_one({'id': page['id']}):
            saved_pages_collection.delete_one({'id': page['id']})
        saved_pages_collection.insert_one(page)


# TODO: add facebook page by exact name that appears in URL, or ID
# TODO: JASON maybe make a pages_utils.py or something rather than sticking it all in events? idk how related they are

def add_facebook_page_from_id(page_id, page_type):
    """
    RULES TO INSERT:
    In General: to GUARANTEE the ID, Inspect Element
    --> under <head> tag, find <meta property=... content="fb://group OR page/?id=<id>">
    ** may need some scrolling
    Pages: can directly use their alias from the URL, in this format: https://www.facebook.com/<page_id>
    Groups: try to use Inspect Element, but if lazy, input the EXACT group title, and this will search and use the first result
    Places: ONLY use Inspect Element, will appear in HTML meta tag as page, search will NOT work
    """
    app_access_token = get_app_token()
    
    # if ID given, always use that
    # call API directly with just the ID, should work
    if page_id:
        return {}

# TODO: add facebook page by exact name that appears in URL, or ID

def add_facebook_page_from_search(search_string, page_type):
    """
    RULES TO INSERT:
    In General: to GUARANTEE the ID, Inspect Element
    --> under <head> tag, find <meta property=... content="fb://group OR page/?id=<id>">
    ** may need some scrolling
    Pages: can directly use their alias from the URL, in this format: https://www.facebook.com/<page_id>
    Groups: try to use Inspect Element, but if lazy, input the EXACT group title, and this will search and use the first result
    Places: ONLY use Inspect Element, will appear in HTML meta tag as page, search will NOT work
    """
    app_access_token = get_app_token()
    
    search_args = {
        'limit': '3',   # want small limit, since only expecting 1 page anyway
        'fields': 'name',
        'access_token': app_access_token
    }

    # by here, must have a name to search
    if page_type == 'page':
        # try call API directly, but if not alias, will give error
        # in that case, need to search, try both pages and places
        return {}
    elif page_type == 'group':
        search_args['type'] = 'group'
        return {}
    elif page_type == 'place':
        search_args['type'] = 'place'
        return {}
    return {}

def get_events_from_pages(pages_by_id, days_before, page_debug_mode=False):
    # pages_by_id = {'676162139187001': 'UCLACAC'}
    # dict of event ids mapped to their info, for fast duplicate checking

    app_access_token = get_app_token()

    """
    time_window is tuple of start and end time of searching, since() and until() parameters
    start time VERY IMPORTANT: all events found by search are guaranteed to start after it,
    including the START TIME of the FIRST EVENT of MULTI DAY EVENTS
    e.g. if an event happens weekly starting from 1/1, and the window start time is 1/2,
    those later weekly events will not appear in search at all!

    so trick is: make sure event is searched up before start time passes, extract all
    sub-events (which have own start and end time), store in db and don't delete until
    THOSE start times are passed

    can pass in # days before current time, as search parameter
    """
    time_window = get_event_time_bounds(days_before)
    
    """
    find events in certain time range, get place + attendance info + time + other info
    use FB API's nested queries, get subfields of events by braces and comma-separated keys
    when using format on string, put {{}} for literal curly braces, then inside put variable argument,
    OR here: use nested keys as 'function calls', like fields()
    """

    # event_args = all under the fields parameter in page_call_args
    # can't ask FB to sort events by time, unfortunately
    # but limit of # events on each page is boundless, 100 is definitely enough to cover
    event_args = [
        'events',
        'fields({})'.format(','.join(EVENT_FIELDS)),
        'since({})'.format(time_window[0]),
        'until({})'.format(time_window[1]),
        'limit({})'.format(100)
    ]

    info_desired = ['name', '.'.join(event_args)] # join all event params with periods between
    # ids field added later to search many pages at the same time
    page_call_args = {
        'fields': ','.join(info_desired), # join name and event args
        'access_token': app_access_token
    }

    print('Start searching pages.')
    # page_id = keys to pages_by_id dictionary
    id_list = []
    id_jsons = {}
    # pages_by_id is dict of page IDs to names
    for i, page_id in tqdm(enumerate(pages_by_id)):
        # don't call events too many times, even batched ID requests all count individually
        # rate limiting applies AUTOMATICALLY (maybe? unclear if rate issue or access token issue)
        # if i >= 51:
        #     break

        # specify list of ids to call at once, limited to 50 at a time, and counts as 50 API calls
        # still is faster than individual calls
        id_list.append(page_id)

        # will tell exactly which page might have gone wrong
        if not page_debug_mode:
            if (i+1) % 50 != 0 and i < len(pages_by_id)-1:
                continue

        # print('Checking page {0}'.format(i+1))
        # pass in whole comma separated list of ids
        page_call_args['ids'] = ','.join(id_list)
        resp = s.get(BASE_EVENT_URL, params=page_call_args)
        # print(resp.url)
        if resp.status_code != 200:
            error_json = resp.json()
            print(
                'Error getting events from FB pages, starting at {0}! Status code {1}: {2}'
                .format(pages_by_id[page_id], resp.status_code, error_json['error'].get('message', 'Unknown error.'))
            )
            # DON'T FORGET TO CLEAR THE ID LIST!
            id_list = []
            continue
        curr_jsons = resp.json()
        # pprint(curr_jsons)
        id_jsons.update(curr_jsons)
        id_list = []

    """
    id_jsons is dict from each PAGE ID to all the events on that page
    So, id_jsons.values() takes all "page_id" values (dicts themselves) and turns into list
    FORMAT of id_jsons:
    {
        "page_id_1": {
            "events": {
                "data": [
                    {
                        "hoster": {
                            "id": <page_id>,
                            "name": <page_name>,
                        }
                        <optional> "duplicate_occurrence": True
                        more events info ...
                    },
                    more events ...
                ],
                "paging": {
                    "cursors": {},
                    "next": <URL>,
                    "previous": <URL>
                }
            }
            "id": <page_id>,
            "name": <page_name>
        },
        "page_id_2": { ... },
        ...
    }
    """
    total_events = {}
    for page_info in tqdm(id_jsons.values()):
        host_entity_info = {}

        host_entity_info['id'] = page_info['id']
        host_entity_info['name'] = page_info['name']
        # case where no events to get from this page, at this time
        if 'events' not in page_info:
            continue
        events_list = page_info['events']

        if 'data' not in events_list:
            print('Missing data field from event results of page {0}!'.format(pages_by_id[page_id]))
            continue
        
        # 'event' is a dict of a bunch of attributes for each event
        for event in events_list['data']:
            # don't specifically ignore repeat events, would update dict anyway (instead of duplicating)
            total_events.update(process_event(event, host_entity_info))

    # with open('page_stats.json', 'w') as outfile:
    #     json.dump(total_events, outfile, indent=4, sort_keys=True, separators=(',', ': '))
    return total_events.values()

def process_event(event, host_info, add_duplicate_tag=False):
    """
    takes in event dict ({many attributes: values}), returns dict of event dicts from event id to all info
    passes in other data for manually added fields (NOT from FB, but for our own purposes)
    """
    app_access_token = get_app_token()

    # URL parameters for refreshing / updating events info, including subevents
    sub_event_call_args = {
        'fields': ','.join(EVENT_FIELDS),
        'access_token': app_access_token
    }

    # only want events with the specified accepted location within UCLA
    if 'place' not in event:
        return {}
    event_place_info = event['place']
    if 'location' not in event_place_info and 'name' in event_place_info:
        # many places have location in name only
        # TODO: get these out with ML

        # temp code to gather all place names from events we find
        # no repeats 
        # if unknown_locations_collection.find_one({'location_name': event_place_info['name']}):
        #     return {}

        # unknown_loc_dict = {
        #     'event_id': event['id'],
        #     'event_name': event['name'],
        #     'location_name': event_place_info['name']
        # }
        # unknown_locations_collection.insert_one(unknown_loc_dict)
        return {}
        
    if not entity_in_right_location(event_place_info['location']):
        return {}

    # for when updating old events and transferring manually added tags over
    if add_duplicate_tag:
        event['duplicate_occurrence'] = True

    expanded_event_dict = {}
    # check for multi-day events, need API call again
    if 'event_times' in event:
        # need to call API again for event fields
        # batch call with multiple IDs: slightly faster from less network traffic, Facebook's end
        sub_ids = []
        for sub_event_header in event['event_times']:
            sub_ids.append(sub_event_header['id'])
        sub_event_call_args['ids'] = ','.join(sub_ids)

        resp = s.get(BASE_EVENT_URL, params=sub_event_call_args)
        # print(resp.url)
        if resp.status_code != 200:
            print(
                'Error trying to retrieve sub-event data of event {0}: Status code {1}'
                .format(event['id'], resp.status_code)
            )
            # just skip this multi-day event if sub-events not successfully retrieved
            return {}
        expanded_event_dict = resp.json()
        # add special "duplicate_occurrence" tag for event occurrences in the future that
        # won't be searchable, because the 1st event start time has passed already
        # don't need to refresh for the 1st event, since that matches the total event start time
        for sub_event in expanded_event_dict.values():
            # using dict.values() and editing each item in list still changes original dictionary
            if sub_event['start_time'] != event['start_time']:
                sub_event['duplicate_occurrence'] = True
    else:
        expanded_event_dict.update({event['id']: event})

    # final cleaning of all event instances, including repeated occurrences
    for event_occurrence in expanded_event_dict.values():
        # clean the category attribute if needed
        if 'category' in event_occurrence:
            if event_occurrence['category'].startswith('EVENT_'):
                event_occurrence['category'] = event_occurrence['category'][6:]
            elif event_occurrence['category'].endswith('_EVENT'):
                event_occurrence['category'] = event_occurrence['category'][:-6]
        # save from which page / group this event was found
        event_occurrence['hoster'] = host_info

        # for debugging: save when each event was updated, in LA time
        current_time = datetime.datetime.now(tzlocal()).astimezone(pytz.timezone('America/Los_Angeles'))
        # get up to microseconds with %f, probably not needed but just in case
        event_occurrence['time_updated'] = current_time.strftime('%Y-%m-%d %H:%M:%S.%f')
    return expanded_event_dict

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

def update_current_events(events, days_before=BASE_EVENT_START_BOUND):
    """
    update events currently in database before new ones put in
    means remove ones too old and re-search the rest
    events = list of complete event dicts
    """
    # for multi-day events that were found a long time ago, have to recall API to check for updates (e.g. cancelled)
    # to tell if multi-day event, check "duplicate_occurrence" tag
    print('Go through currently stored events to update.')
    kept_events = {}
    for event in tqdm(events):
        if not time_in_past(event['start_time'], days_before):
            updated_event_dict = process_event(event, event.get('hoster', '<NONE, UPDATE>'), event.get('duplicate_occurrence', False))
            kept_events.update(updated_event_dict)
    # return a dict of kept event IDs to their info
    return kept_events

def get_facebook_events(days_before=BASE_EVENT_START_BOUND):
    """
    search for UCLA-associated places and groups, using existing list on DB
    """
    pages_by_id = {}
    for page in saved_pages_collection.find():
        pages_by_id[page['id']] = page['name']

    # turn event ID dict to array of their values
    all_events = get_events_from_pages(pages_by_id, days_before)
    # need to wrap the array of event infos in a dictionary with 'events' key, keep format same as before
    total_event_object = {'events': all_events, 'metadata': {'events': len(all_events)}}
    print("Total event count: {0}".format(len(all_events)))
    return total_event_object

def find_many_events():
    unknown_locations_collection.delete_many({})
    """
    find events up to 2 years ago
    """
    raw_events = get_facebook_events(730)
    # still the dumb but simple update method
    events_ml_collection.delete_many({})
    events_ml_collection.insert_many(raw_events['events'])
    print('Found {0} events'.format(raw_events['metadata']['events']))

if __name__ == '__main__':
    res = get_facebook_events()
    pprint(res['events'][:3])
    
    # find_many_events()

    # add_pages_from_json('holy_groups.json')
    # add_pages_from_json('holy_pages.json')

