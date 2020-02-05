from mappening.utils.secrets import FACEBOOK_USER_ACCESS_TOKEN

import sys
import requests
import datetime, dateutil.parser, pytz
from tqdm import tqdm   # a progress bar, pretty

# Need this to run file locally, or else won't know where to find mappening.utils.*
sys.path.insert(0, './../../..')

# Specify version in case most updated version (default if not specified) removes functionality, causing errors
API_VERSION_STR = 'v5.0/'
BASE_URL = 'https://graph.facebook.com/' + API_VERSION_STR

# Got APP_ID and APP_SECRET from Mappening app with developers.facebook.com
ACCESS_TOKEN_URL = BASE_URL + 'oauth/access_token'

BASE_ME_URL = BASE_URL + "me/events/"

# Id is ALWAYS returned, for any field, explicitly requested or not, as long as there is data
# added 'owner' and 'id'
# UPDATE: The following event fields are the only fields that don't restrict the events
# returned from ~900 to ~70. For some reason, asking for "owner", "category", and some others
# causes the Facebook API to only return a few events (even tho every event has an owner??)
EVENT_FIELDS = ['id', 'name', 'cover', 'description', 'start_time', 'end_time',
                'place', 'event_times']


s = requests.Session()

def get_event_time_bounds(days_before):
    # back_jump = 60         # for repeating events that started a long time ago
    back_jump = days_before  # arbitrarily allow events that start 1 day ago (allows refresh to keep current day's events)
    forward_jump = 60        # and 60 days into the future
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

    event_args = {
        'fields': ','.join(EVENT_FIELDS),
        'access_token': app_access_token,
        'limit': 100
    }

    events = []

    page_num = 0
    total = 0
    curr_url = BASE_ME_URL

    while curr_url:

        # only need params on first get ?
        resp = s.get(curr_url, params=event_args)

        if resp.status_code != 200:
            print(
                'Error getting interested events, on results page {0}! Status code {1}'
                .format(page_num, resp.status_code)
            )
            print(resp.json())
            break

        data = resp.json()

        try:
            events += data['data']

            total += len(data['data'])
            curr_url = data['paging']['next']

            # print (curr_url)

            page_num += 1
        except KeyError:
            break

        # print(page_num)
        # print(resp.json())

    print(f"collected {len(events)} events from facebook")

    return events
