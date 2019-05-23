accessToken = 'EAAFB1Et4EnkBAORaxZBTxcCuBNZBCVt7U2hF7R2Lhn832ZC8cSF0FSwLLNaXxHtYkhFDpm6ieux7TwgZB1igYa0Sejy8wxRZAA8xxxuyMQZB4qj6HZAwRU6FbezcSSeaJkih4NvcPB3DB3tcITEjGgwzwjt3MdkA8cEsskruNxCWW8ctjFSUYvO3M3WOtiDlPgweQ8OQUos4KR6oXZC3PLLgVqWs0H10jv3u7tVQNque1gZDZD'

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

from mappening.utils.database import events_fb_puppeteer_collection
from mappening.utils.secrets import FACEBOOK_USER_ACCESS_TOKEN

import facebook

def facebook_scrape():

    # graph = facebook.GraphAPI(access_token=accessToken) 

    # selim's facebook id
    event = graph.get_object(id='100035494397802',
                            fields='events')

    print('events from selim')
    print(event['events'])

    # insert_one a event object
    # events_fb_puppeteer_collection.insert_one({'id': page_id, 'name': page_name})

    # TODO change it
    return 1


