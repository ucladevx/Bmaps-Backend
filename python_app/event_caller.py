import requests
import json
import time, datetime
from pprint import pprint
import json

data = json.load(open('secrets.json'))

# Specify version in case most updated version (default if not specified) removes functionality, causing errors
API_VERSION_STR = 'v2.10/'
BASE_URL = 'https://graph.facebook.com/' + API_VERSION_STR

# Got APP_ID and APP_SECRET from Mappening app with developers.facebook.com
FACEBOOK_APP_ID = data['FACEBOOK_APP_ID']
FACEBOOK_APP_SECRET = data['FACEBOOK_APP_SECRET']
ACCESS_TOKEN_URL = BASE_URL + 'oauth/access_token'

SEARCH_URL = BASE_URL + 'search'

# Updated coordinates of Bruin Bear
CENTER_LATITUDE = 34.070966
CENTER_LONGITUDE = -118.445
SEARCH_TERMS = ['ucla', 'bruin', 'ucla theta', 'ucla kappa', 'campus events commission']
UCLA_ZIP_STRINGS = ['90024', '90095']

# Get events by adding page ID and events field
BASE_EVENT_URL = BASE_URL

# Id is ALWAYS returned, for any field, explicitly requested or not, as long as there is data
EVENT_FIELDS = ['name', 'category', 'place', 'description', 'start_time', 'end_time',
                'attending_count', 'maybe_count', 'interested_count', 'noreply_count', 'is_canceled',
                'ticket_uri', 'cover']

s = requests.Session()

def format_time(time):
    # %z gets time zone difference in +/-HHMM from UTC
    return time.strftime('%Y-%m-%d %H:%M:%S %z')

def get_event_time_bounds():
    back_jump = 0       # arbitrarily allow events that start TODAY (0 days ago)
    forward_jump = 60   # and 60 days into the future
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
    return resp.json()['access_token']

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

# for searching all types: place, page, and group
def find_ucla_entities(app_access_token):
    ucla_entities = {}
    page_search_args = {
        'type': 'page',
        'limit': '500',     # limit is as high as desired, but these searches top out at ~350 entries now
        'fields': 'name,location',
        'access_token': app_access_token
    }
    for term in SEARCH_TERMS:
        page_search_args['q'] = term

        resp = s.get(SEARCH_URL, params=page_search_args)
        if resp.status_code != 200:
            print(
                'Error searching for pages with term {0}! Status code {1}'
                .format(term, resp.status_code)
            )
            break
        elif 'data' not in resp.json():
            print('Page search results missing data field!')
            break

        for page in resp.json()['data']:
            # filter out pages definitely not near UCLA
            # if no location, must keep for now, else check its location
            if 'location' not in page or entity_in_right_location(page['location']):
                ucla_entities[page['id']] = page['name']



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

def get_events_from_pages(pages_by_id, app_access_token):
    # dict of event ids mapped to their info, for fast duplicate checking
    total_events = {}
    # time_window is tuple of start and end time, right now end not used (all the way to future)
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
    for i, page_id in enumerate(pages_by_id):
        # don't call events too many times, even batched ID requests all count individually
        # rate limiting applies AUTOMATICALLY (maybe? unclear if rate issue or access token issue)
        # if i >= 51:
        #     break

        # specify list of ids to call at once, limited to 50 at a time, and counts as 50 API calls
        # still is faster than individual calls
        
        if (i+1) % 50 != 0 and i < len(pages_by_id)-1:
            id_list.append(page_id)
            continue

        # id_list.append(page_id)

        print('Checking page {0}'.format(i+1))
        # pass in whole comma separated list of ids
        page_call_args['ids'] = ','.join(id_list)
        resp = s.get(BASE_EVENT_URL, params=page_call_args)
        id_list = []
        # print(resp.url)
        if resp.status_code != 200:
            print(
                'Error getting events from FB pages, starting at {0}! Status code {1}'
                .format(pages_by_id[page_id], resp.status_code)
            )
            break
        id_jsons.update(resp.json())

    page_event_counts = {}
    for page_info in id_jsons.values():
        if 'events' not in page_info:
            # no events = 0 count
            page_event_counts[page_info['name']] = 0
            continue
        events_list = page_info['events']

        if 'data' not in events_list:
            print('Missing data field from event results of page {0}!'.format(pages_by_id[page_id]))
            continue

        # only want events with the specified accepted location within UCLA
        # event is a dict of a bunch of attributes for each event
        event_count = 0
        for event in events_list['data']:
            if 'place' not in event or 'location' not in event['place']:
                # many places have location in name only, TODO: get these out
                continue
            if entity_in_right_location(event['place']['location']):
                event_count += 1    # count any events associated to current page, in actual location
                if event['id'] not in total_events:
                    if 'category' in event:
                        if event['category'].startswith('EVENT_'):
                            event['category'] = event['category'][6:]
                        elif event['category'].endswith('_EVENT'):
                            event['category'] = event['category'][:-6]
                    total_events[event['id']] = event
        # only count "useful" events: actually located around UCLA
        page_event_counts[page_info['name']] = event_count
    with open('page_stats.json', 'w') as outfile:
        json.dump(page_event_counts, outfile, indent=4, sort_keys=True, separators=(',', ': '))
    return total_events.values()

def get_facebook_events():
    app_access_token = get_app_token()
    
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
    get_facebook_events()

