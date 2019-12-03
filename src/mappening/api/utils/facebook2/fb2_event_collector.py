# from mappening.utils.database import fb_pages_saved_collection, fb_pages_ignored_collection, unknown_locations_collection
from mappening.utils.secrets import FACEBOOK_USER_ACCESS_TOKEN

import os
import sys
import requests
import json
import time, datetime, dateutil.parser, pytz
from dateutil.tz import tzlocal
from pprint import pprint
from tqdm import tqdm   # a progress bar, pretty

# from definitions import CENTER_LATITUDE, CENTER_LONGITUDE, BASE_EVENT_START_BOUND

# Need this to run file locally, or else won't know where to find mappening.utils.*
sys.path.insert(0, './../../..')

# Specify version in case most updated version (default if not specified) removes functionality, causing errors
API_VERSION_STR = 'v5.0/'
BASE_URL = 'https://graph.facebook.com/' + API_VERSION_STR

# Got APP_ID and APP_SECRET from Mappening app with developers.facebook.com
ACCESS_TOKEN_URL = BASE_URL + 'oauth/access_token'

SEARCH_URL = BASE_URL + 'search'

SEARCH_TERMS = ['ucla', 'bruin', 'ucla theta', 'ucla kappa', 'ucla beta']
UCLA_ZIP_STRINGS = ['90024', '90095']

# Get events by adding page ID and events field
BASE_EVENT_URL = BASE_URL

BASE_ME_URL = BASE_URL + "me/"

# Id is ALWAYS returned, for any field, explicitly requested or not, as long as there is data
# added 'owner' and 'id'
EVENT_FIELDS = ['name', 'category', 'place', 'description', 'start_time', 'end_time', 'event_times',
                'attending_count', 'maybe_count', 'interested_count', 'noreply_count', 'is_canceled',
                'ticket_uri', 'cover', 'owner', 'id']


s = requests.Session()

def get_event_time_bounds(days_before):
    # back_jump = 60        # for repeating events that started a long time ago
    back_jump = days_before # arbitrarily allow events that start 1 day ago (allows refresh to keep current day's events)
    forward_jump = 60       # and 60 days into the future
    now = datetime.datetime.now()
    before_time = now - datetime.timedelta(days=back_jump)
    after_time = now + datetime.timedelta(days=forward_jump)
    return ((before_time).strftime('%Y-%m-%d %H:%M:%S %z'), (after_time).strftime('%Y-%m-%d %H:%M:%S %z'))


def get_interested_events(days_before=0):
    """
    Gets all events marked as interested by the fake Bmaps account "Selim Alpay"
    """

    app_access_token = FACEBOOK_USER_ACCESS_TOKEN

    time_window = get_event_time_bounds(days_before)

    event_args = [
        'events',
        'fields({})'.format(','.join(EVENT_FIELDS)),
        'since({})'.format(time_window[0]),
        'until({})'.format(time_window[1]),
        'limit({})'.format(1000) # not sure what the best limit is
    ]

    info_desired = ['name', '.'.join(event_args)] # join all event params with periods between
    # ids field added later to search many pages at the same time


    place_search_args = {
        'fields': "events.limit(100){category,cover,description,start_time,is_canceled,name,owner,updated_time,id,place,maybe_count,noreply_count,interested_count,attending_count,end_time,event_times}",
        'access_token': app_access_token
    }

    events = []   

    page_num = 0
    curr_url = BASE_ME_URL
    while page_num < 10:

        # only need params on first get ?
        if page_num == 0:
            resp = s.get(curr_url, params=place_search_args)
        else:
            resp = s.get(curr_url)

        if resp.status_code != 200:
            print(
                'Error getting interested events, on results page {0}! Status code {1}'
                .format(page_num, resp.status_code)
            )
            break

        responses = resp.json()

        # print(responses)

        # first request has "events" field, subsequent requests don't
        if 'events' in responses:
            data = responses['events']
        else:
            data = responses

        if 'data' not in data:
            print('Missing events field from interested events search results!')
            break

        # now we have all the facebook event data
        # we have to clean it up before we insert it into the database
        # so it is the same as the eventbrite events and it has the free food tag

        # we have to modify the event_processor to copy eb_event_processor
        # that's where we will insert into the database
        events += data['data']
        
        # check if there is a next page of results
        if 'paging' not in data or 'next' not in data['paging']:
            # no more responses
            break
        else:
            curr_url = data['paging']['next']
        page_num += 1

    # a dictionary, to keep only unique pages
    return events
