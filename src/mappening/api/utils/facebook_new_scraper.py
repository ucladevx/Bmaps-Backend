## DONT USE THIS ONE

'''
In this file, I want to query the Facebook Graph API to get the event objects that the Mappening Facebook Account (Selim Alpay) is interested in.
Once I have those event objects, I want to push them to the test data facebook collection
'''

import requests
import json
import time, datetime, dateutil.parser, pytz
from dateutil.tz import tzlocal
from pprint import pprint
from tqdm import tqdm   # a progress bar, pretty


# for sys.exit()
import os

# from definitions import CENTER_LATITUDE, CENTER_LONGITUDE, BASE_EVENT_START_BOUND

# need this to run file locally, or else won't know where to find mappening.utils.*
import sys
sys.path.insert(0, './../../..')

from mappening.utils.database import events_fb_test_collection
from mappening.utils.secrets import FACEBOOK_USER_ACCESS_TOKEN_2

import facebook

def facebook_scrape():

    graph = facebook.GraphAPI(access_token=FACEBOOK_USER_ACCESS_TOKEN_2) 

    # Selim Alpay's Facebook ID
    profile = graph.get_object(id='100035494397802')

    events = graph.get_connections("me", "events")

    # Print Events Json to the screen
    events_json = json.dumps(events['data'])
    print('got following events from Selim Alpay, mappening test account')
    print(events_json)

    events_fb_test_collection.insert_one(events)

