from mappening.utils.database import events_eventbrite_collection
from mappening.utils.secrets import EVENTBRITE_USER_KEY

import os
import sys
import time, datetime
from pprint import pprint
from tqdm import tqdm
import json
import requests
from flask import jsonify
import eventbrite

# eventbrite = eventbrite.Eventbrite(EVENTBRITE_USER_KEY)

from definitions import CENTER_LATITUDE, CENTER_LONGITUDE

sys.path.insert(0, './../../..')

# Use this as reference for now
EVENT_FIELDS = ['name', 'category', 'place', 'description', 'start_time', 'end_time', 'event_times',
                'attending_count', 'maybe_count', 'interested_count', 'noreply_count', 'is_canceled',
                'ticket_uri', 'cover']

"""
Categories for reference, as of May 2018: Full Name [Short Name, if any]
fewer than Facebook (many pairs consolidated)

Music | Business & Professional [Business] | Food & Drink | Community & Culture [Community] |
Performing & Visual Arts [Arts] | Film, Media & Entertainment [Film & Media] | Sports & Fitness |
Health & Wellness [Health] | Science & Technology [Science & Tech] | Travel & Outdoor | Charity & Causes |
Religion & Spirituality [Spirituality] | Family & Education | Seasonal & Holiday [Holiday] |
Government & Politics [Government] | Fashion & Beauty [Fashion] | Home & Lifestyle | Auto, Boat & Air |
Hobbies & Special Interest [Hobbies] | Other | School Activities
"""

# TODO: like other APIs, split this method up
# 1st part = get raw data and put in DB (updating repeats), 2nd part = process for events_current_processed

# Get the raw data 
# Put in DB and update repeats 
# Process events 
def get_raw_events(days_back_in_time):
    days_back = days_back_in_time
    days_forward = 90
    now = datetime.datetime.now()
    past_bound = (now - datetime.timedelta(days=days_back)).strftime('%Y-%m-%dT%H:%M:%S')
    future_bound = (now + datetime.timedelta(days=days_forward)).strftime('%Y-%m-%dT%H:%M:%S')

    # session = requests.Session()

    eb = eventbrite.Eventbrite(EVENTBRITE_USER_KEY)

    # personal_token = EVENTBRITE_USER_KEY
    # base_endpoint = 'https://www.eventbriteapi.com/v3'
    # sample_headers = {
    #     'Authorization': 'Bearer ' + personal_token,
    # }

    # Most events on 1 page = 50, want more
    # page_num = 1
    # request_new_results = True

    # events_search_ep = '/events/search'
    search_args = {
        "location.latitude": CENTER_LATITUDE,
        "location.longitude": CENTER_LONGITUDE,
        "location.within": "1mi",
        "start_date.range_start": past_bound,
        "start_date.range_end": future_bound,
        "sort_by": "best"
    }

    response = eb.event_search(**search_args)

    # print(response)

    all_events = response.get('events')

    # TODO: We need to add pagination back. Cindy can try scheduling this to get
    # each page after every 10 minutes until has_more_items is false
    # to get around rate limiting.

    # Loop through returned pages of events until no more, or enough
    # while request_new_results and page_num <= 20:

    #     response = eventbrite2.event_search(**search_args)

    #     print(response)
 
    #     # There's always a 1st page result that works
    #     search_args["page"] = page_num
    #     print("search_args")
    #     print(search_args)
    #     # responseSession = session.get(
    #     #     base_endpoint + events_search_ep,
    #     #     headers = sample_headers,
    #     #     verify = True,  # Verify SSL certificate
    #     #     params = search_args,
    #     # ).json()


    #     # print(responseSession)
    #     # print(responseSession.text)
        
    #     # Extend, not append!
    #     # combines elements of two lists as expected vs adds in the new list as ONE element
    #     all_events.extend(response.get('events'))
    #     if 'pagination' in response and response['pagination']['has_more_items']:
    #         request_new_results = True
    #         page_num += 1
    #     else:
    #         request_new_results = False

    # print('Finished collecting Eventbrite events!')
    return all_events

# Database updating 
def update_database(all_events):
    personal_token = EVENTBRITE_USER_KEY
    base_endpoint = 'https://www.eventbriteapi.com/v3'
    sample_headers = {
        'Authorization': 'Bearer ' + personal_token
    }
    
    # TODO: replace deleting all events and then reinserting events with smart
    # updating. Delete those not present, update those that already exist.
    events_eventbrite_collection.delete_many({})
    events_eventbrite_collection.insert_many(all_events)

    print('inserted properly')

    all_cat_ep = '/categories'
    session = requests.Session()
    cat_resp = session.get(
        base_endpoint + all_cat_ep,
        headers = sample_headers,
        verify = True,
    )
    # List of dicts, 1 per category (with ID and name, full and shorthand)
    all_categories = {}
    raw_categories = cat_resp.json().get('categories')

    # TODO: temp solution: throw away Eventbrite category to use ML model trained on Facebook
    for raw_cat in raw_categories:
        used_name = raw_cat['short_name']
        all_categories[raw_cat['id']] = {'full_name': raw_cat['name'], 'short_name': used_name}

    print('Finished updating Eventbrite events!')
