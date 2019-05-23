accessToken = 'EAAFB1Et4EnkBAEbG2jpySE1LaXB8eL9FNmI4ouaFoGyIoso1UxeAnfhNawFdTgBla2CJso5ZAk0gABhrzW1r0pYQssR0A4cIoVuLNzoNOE4VRet8tOid3slVLJSGzcfkJabhJ3izUuZCuZAy1Ashlm7QymxZC5xaQuXIll4Y21cfRUAR8MwPTSZBNjkAFqSH8Kjqk8SZC3YIzkUrVafDnJDcW0yjlFMpPpYFW6lZBqaPgZDZD'

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

# need this to run fcile locally, or else won't know where to find mappening.utils.*
import sys
sys.path.insert(0, './../../..')

from mappening.utils.database import events_fb_test_collection
from mappening.utils.secrets import FACEBOOK_USER_ACCESS_TOKEN

import facebook

def facebook_scrape():

    # graph = facebook.GraphAPI(access_token=accessToken) 

    # haki's facebook id
    event = graph.get_object(id='100003804778237',
                            fields='events')

    print('events from haki')
    print(event['events'])

    # insert_one a event object
    # events_fb_test_collection.insert_one({'id': page_id, 'name': page_name})
