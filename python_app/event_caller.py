import requests
import json
import time, datetime
from pprint import pprint
import json

# for sys.exit()
import sys
import os

# for testing just this file
# COMMENT IT OUT IF RUNNING DOCKER
from dotenv import load_dotenv

# Get environment vars for keeping sensitive info secure
# Has to come before blueprints that use the env vars
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)


# Specify version in case most updated version (default if not specified) removes functionality, causing errors
API_VERSION_STR = 'v2.10/'
BASE_URL = 'https://graph.facebook.com/' + API_VERSION_STR

# Got APP_ID and APP_SECRET from Mappening app with developers.facebook.com
USER_ACCESS_TOKEN = os.getenv('FACEBOOK_USER_ACCESS_TOKEN')
FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID')
FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET')
ACCESS_TOKEN_URL = BASE_URL + 'oauth/access_token'

SEARCH_URL = BASE_URL + 'search'

# Updated coordinates of Bruin Bear
CENTER_LATITUDE = 34.070966
CENTER_LONGITUDE = -118.445
SEARCH_TERMS = ['ucla', 'bruin', 'ucla theta', 'ucla kappa', 'ucla beta',
                'campus events commission', 'foundations choreography', 'cssaucla']
UCLA_ZIP_STRINGS = ['90024', '90095']

# Get events by adding page ID and events field
BASE_EVENT_URL = BASE_URL

# Id is ALWAYS returned, for any field, explicitly requested or not, as long as there is data
EVENT_FIELDS = ['name', 'category', 'place', 'description', 'start_time', 'end_time', 'event_times',
                'attending_count', 'maybe_count', 'interested_count', 'noreply_count', 'is_canceled',
                'ticket_uri', 'cover']

s = requests.Session()

def format_time(time):
    # %z gets time zone difference in +/-HHMM from UTC
    return time.strftime('%Y-%m-%d %H:%M:%S %z')

def get_event_time_bounds(days_before=1):
    # back_jump = 60        # for repeating events that started a long time ago
    back_jump = days_before # arbitrarily allow events that start 1 day ago (allows refresh to keep current day's events)
    forward_jump = 60       # and 60 days into the future
    now = datetime.datetime.now()
    before_time = now - datetime.timedelta(days=back_jump)
    after_time = now + datetime.timedelta(days=forward_jump)
    return (format_time(before_time), format_time(after_time))

def get_app_token():
    token_args = {
        'client_id': FACEBOOK_APP_ID,
        'client_secret': FACEBOOK_APP_SECRET,
        'grant_type': 'client_credentials'
    }
    resp = s.get(ACCESS_TOKEN_URL, params=token_args)
    if resp.status_code != 200:
        print('Error in getting access code! Status code {}'.format(resp.status_code))
        return ''
    # don't use app access token for now, not allowed to search groups
    # return resp.json()['access_token']
    return USER_ACCESS_TOKEN

# if zip code, check in UCLA zip codes (first 5 digits)
# if no zip code, check that in Los Angeles, CA
def entity_in_right_location(loc_data):
    if 'zip' in loc_data:
        zip_string = loc_data['zip'][:5]
        if zip_string in UCLA_ZIP_STRINGS:
            return True
    elif 'city' in loc_data and 'state' in loc_data:
        if loc_data['city'] == 'Los Angeles' and loc_data['state'] == 'CA':
            return True
    return False

def general_search_results(search_term, search_args):
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

# for searching all types: place, page, and group
def find_ucla_entities(app_access_token):
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

    return ucla_entities

# TODO: add facebook page by exact name that appears in URL, or ID
"""
RULES TO INSERT:
In General: to GUARANTEE the ID, Inspect Element
    --> under <head> tag, find <meta property=... content="fb://group OR page/?id=<id>">
    ** may need some scrolling
Pages: can directly use their alias from the URL, in this format: https://www.facebook.com/<page_id>
Groups: try to use Inspect Element, but if lazy, input the EXACT group title, and this will search and use the first result
Places: ONLY use Inspect Element, will appear in HTML meta tag as page, search will NOT work
"""
def add_facebook_page(page_type='group', id='', name=''):
    page_id = str(id)
    # convert integer IDs to strings
    # if no info given then just don't do anything
    if not page_id and not name:
        return {}

    app_access_token = get_app_token()
    
    # if ID given, always use that
    # call API directly with just the ID, should work
    if page_id:
        return {}

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

def get_events_from_pages(pages_by_id, app_access_token):
    # pages_by_id = {'676162139187001': 'UCLACAC'}
    # dict of event ids mapped to their info, for fast duplicate checking
    total_events = {}
    # time_window is tuple of start and end time of searching, since() and until() parameters
    # start time VERY IMPORTANT: all events found by search are guaranteed to start after it,
    # including the START TIME of the FIRST EVENT of MULTI DAY EVENTS
    # e.g. if an event happens weekly starting from 1/1, and the window start time is 1/2,
    # that event will not appear at all!

    # so trick is: make sure event is searched up before start time passes, extract all
    # sub-events (which have own start and end time), store in db and don't delete until
    # THOSE start times are passed

    # can pass in # days before now to include in search, too
    time_window = get_event_time_bounds()
    
    # find events in certain time range, get place + attendance info + time + other info
    # use FB API's nested queries, get subfields of events by braces and comma-separated keys
    # when using format on string, put {{}} for literal curly braces, then inside put variable argument,
    # OR here: use nested keys as 'function calls', like fields()

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
    for i, page_id in enumerate(pages_by_id):
        # don't call events too many times, even batched ID requests all count individually
        # rate limiting applies AUTOMATICALLY (maybe? unclear if rate issue or access token issue)
        # if i >= 51:
        #     break

        # specify list of ids to call at once, limited to 50 at a time, and counts as 50 API calls
        # still is faster than individual calls
        id_list.append(page_id)
        if (i+1) % 50 != 0 and i < len(pages_by_id)-1:
            continue

        print('Checking page {0}'.format(i+1))
        # pass in whole comma separated list of ids
        page_call_args['ids'] = ','.join(id_list)
        resp = s.get(BASE_EVENT_URL, params=page_call_args)
        # print(resp.url)
        if resp.status_code != 200:
            print(
                'Error getting events from FB pages, starting at {0}! Status code {1}'
                .format(pages_by_id[page_id], resp.status_code)
            )
            break
        curr_jsons = resp.json()
        # pprint(curr_jsons)
        id_jsons.update(curr_jsons)
        id_list = []

    # URL parameters for extra API calls of multi day events
    sub_event_call_args = {
        'fields': ','.join(EVENT_FIELDS),
        'access_token': app_access_token
    }
    all_entity_info = []

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
    for page_info in id_jsons.values():
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
        # only want events with the specified accepted location within UCLA
        # 'event' is a dict of a bunch of attributes for each event
        for event in events_list['data']:
            if 'place' not in event or 'location' not in event['place']:
                # many places have location in name only, TODO: get these out with ML
                continue
            if entity_in_right_location(event['place']['location']):
                # check for multi-day events, need API call again
                sub_event_list = []
                if 'event_times' in event:
                    # need to call URL with reduced arguments, since most info is same as main event
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
                        continue
                    sub_event_list = resp.json().values()
                    # add special "API_refresh" tag for event occurrences in the future that
                    # won't be searchable, because the 1st event start time has passed already
                    # don't need to refresh for the 1st event, since that matches the total event start time
                    for e, sub_event in enumerate(sub_event_list):
                        if sub_event['start_time'] != event['start_time']:
                            sub_event['API_refresh'] = True
                else:
                    sub_event_list.append(event)

                for event_occurrence in sub_event_list:
                    if event_occurrence['id'] not in total_events:
                        # clean the category attribute if needed
                        if 'category' in event_occurrence:
                            if event_occurrence['category'].startswith('EVENT_'):
                                event_occurrence['category'] = event_occurrence['category'][6:]
                            elif event_occurrence['category'].endswith('_EVENT'):
                                event_occurrence['category'] = event_occurrence['category'][:-6]
                        # save from which page / group this event was found
                        event_occurrence['hoster'] = host_entity_info
                        total_events[event_occurrence['id']] = event_occurrence

    # with open('page_stats.json', 'w') as outfile:
    #     json.dump(all_entity_info, outfile, indent=4, sort_keys=True, separators=(',', ': '))
    return total_events.values()

# called from events.py AFTER get_facebook_events, app_access_token passed back in from events.py
# event_ids_to_entities = dict, all event IDs relevant mapped to all their hosting page info dicts
def update_current_events(event_ids_to_entities):
    app_access_token = get_app_token()

    sub_event_call_args = {
        'fields': ','.join(EVENT_FIELDS),
        'access_token': app_access_token
    }
    # take out the IDs (keys) of the events dict
    sub_event_call_args['ids'] = ','.join(event_ids_to_entities.keys())
    resp = s.get(BASE_EVENT_URL, params=sub_event_call_args)
    # print(resp.url)
    if resp.status_code != 200:
        print('Error trying to update data of current multi-day events: Status code {0}'.format(resp.status_code))
        # return empty list: couldn't get any updated info
        return []
    sub_event_dict = resp.json()
    # add back in the "hoster" attribute of each event (info about the page that posted the event)
    for event_key in sub_event_dict:
        sub_event_dict[event_key]["hoster"] = event_ids_to_entities[event_key]
    # turn dict into list
    return sub_event_list.values()

def get_facebook_events():
    app_access_token = get_app_token()
    # app_access_token = USER_ACCESS_TOKEN
    
    # search for UCLA-associated places and groups
    # limit to as high as possible, go until no pages left
    # type = places: give center coordinates (of Bruin Bear), distance 1000 (in meters), limit max 100
    # type = pages: search with reserved terms, limit = 1000, check location as well
    # 2 types of places: ones with events, ones without, cannot do anything about without events
    # pre-filtering: only store places / pages with UCLA zip code, or LA CA, or no place at all (filter events later)
    pages_by_id = find_ucla_entities(app_access_token)

    # turn event ID dict to array of their values
    all_events = get_events_from_pages(pages_by_id, app_access_token)
    # need to wrap the array of event infos in a dictionary with 'events' key, keep format same as before
    total_event_object = {'events': all_events, 'metadata': {'events': len(all_events)}}
    return total_event_object

if __name__ == '__main__':
    res = get_facebook_events()
    pprint(res['events'][:10])
    print("Total event count: {0}".format(res['metadata']['events']))

