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

s = requests.Session()

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

# Eventbrite closed their event search in December 2019, now we have to hardcode the venue ids and find events through each one
# This also means we don't really need to worry about pagination because each venue doesn't have enough events to be paginated.
venue_ids = [23819658,
             29902700,
             36549987,
             36766165,
             37513703,
             38085179,
             39006121,
             39718935,
             40055415,
             40130169,
             40304155,
             40632529,
             40783475,
             41096995,
             41196205,
             41197033,
             41454477,
             41465307,
             41531729,
             41682667,
             41872749,
             41950517,
             42142291,
             42452299,
             42543427,
             42556307,
             42638817,
             42703699,
             42779809,
             43003357,
             43066275,
             43182603,
             43218439,
             43270877,
             43288447,
             43291911,
             43465913,
             43507461,
             43523745,
             43773109,
             43790291,
             44044679,
             44187749,
             44273031,
             44276537,
             44281423,
             44328647]


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

    all_events = []
    for venue_id in venue_ids:

        headers = {
            'Authorization': 'Bearer ' + EVENTBRITE_USER_KEY
        }
        # request = Request(f'https://www.eventbriteapi.com/v3/venues/{venue_id}/events/?status=live&order_by=start_asc&start_date=&only_public=true', headers=headers)

        # old search args:
        # search_args = {
        #     "location.latitude": CENTER_LATITUDE,
        #     "location.longitude": CENTER_LONGITUDE,
        #     "location.within": "1mi",
        #     "start_date.range_start": past_bound,
        #     "start_date.range_end": future_bound,
        #     "sort_by": "best"
        # }

        params = {
            "status": "live",
            "order_by": "start_asc",
            "start_date.range_start": past_bound,
            "start_date.range_end": future_bound,
            "only_public": True
        }

        response = s.get(f'https://www.eventbriteapi.com/v3/venues/{venue_id}/events', params=params, headers=headers)
        # print(response)
        # print(response.json())
        all_events.extend(response.json()['events'])

    # print("all_events")
    # print(all_events)
    print(len(all_events))


    print('Finished collecting Eventbrite events!')
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
