import time, datetime
from pprint import pprint
from tqdm import tqdm
import json
import requests

import os

import sys
sys.path.insert(0, './../../..')
from mappening.utils.database import events_eventbrite_collection, events_current_processed_collection
from mappening.utils.secrets import EVENTBRITE_USER_KEY

# to map all Eventbrite categories to Facebook ones
from mappening.ml.autocategorization import categorizeEvents

from definitions import CENTER_LATITUDE, CENTER_LONGITUDE, API_UTILS_PATH

# use this as reference for now
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
def entire_eventbrite_retrieval(days_back_in_time):
    days_back = days_back_in_time
    days_forward = 90
    now = datetime.datetime.now()
    past_bound = (now - datetime.timedelta(days=days_back)).strftime('%Y-%m-%dT%H:%M:%S')
    future_bound = (now + datetime.timedelta(days=days_forward)).strftime('%Y-%m-%dT%H:%M:%S')

    session = requests.Session()

    personal_token = EVENTBRITE_USER_KEY
    base_endpoint = 'https://www.eventbriteapi.com/v3'
    sample_headers = {
        'Authorization': 'Bearer ' + personal_token
    }

    # most events on 1 page = 50, want more
    page_num = 1
    request_new_results = True

    events_search_ep = '/events/search'
    search_args = {
        'location.latitude': CENTER_LATITUDE,
        'location.longitude': CENTER_LONGITUDE,
        'location.within': '1mi',
        'start_date.range_start': past_bound,
        'start_date.range_end': future_bound,
        'sort_by': 'best'
    }

    all_events = []
    # loop through returned pages of events until no more, or enough
    while request_new_results and page_num <= 20:
        search_args['page'] = str(page_num)  # there's always a 1st page result that works

        response = session.get(
            base_endpoint + events_search_ep,
            headers = sample_headers,
            verify = True,  # Verify SSL certificate
            params = search_args,
        ).json()
        
        # extend, not append!
        # combines elements of two lists as expected vs adds in the new list as ONE element (no)
        all_events.extend(response.get('events'))
        if 'pagination' in response and response['pagination']['has_more_items']:
            request_new_results = True
            page_num += 1
        else:
            request_new_results = False

    print('done getting eventbrite events!')
    # raw event data insert
    # TODO: the dumb complete reinsertion thing again
    # this should be removed completely: eventbrite_collection accumulates, never deletes
    events_eventbrite_collection.delete_many({})
    events_eventbrite_collection.insert_many(all_events)

    all_cat_ep = '/categories'
    cat_resp = session.get(
        base_endpoint + all_cat_ep,
        headers = sample_headers,
        verify = True,
    )
    # list of dicts, 1 per category (with ID and name, full and shorthand)
    all_categories = {}
    raw_categories = cat_resp.json().get('categories')

    # TODO: temp solution: throw away Eventbrite category to use ML model trained on Facebook
    for raw_cat in raw_categories:
        used_name = raw_cat['short_name']
        all_categories[raw_cat['id']] = {'full_name': raw_cat['name'], 'short_name': used_name}

    all_venues = {}

    cleaned_events = []
    for event_info in tqdm(all_events):
        one_event = {
            'id': event_info.get('id', -1),
            'name': event_info['name']['text'],
            'description': event_info['description']['text'],
            'interested_count': event_info.get('capacity', 0),
            'maybe_count': 0,
            'attending_count': 0,
            'noreply_count': 0,
            'is_canceled': False,
            'cover': {
                'source': event_info['logo']['url'] if event_info['logo'] else '<NONE>',
                'offset_x': 0,
                'offset_y': 0
            },
            # 'category': all_categories[event_info['category_id']]['short_name'] if event_info['category_id'] else '<NONE>',
            'start_time': event_info['start']['local'] + '-0700'
        }
        if 'end' in event_info and 'local' in event_info['end']:
            one_event['end_time'] = event_info['end']['local'] + '-0700'

        # finding place: takes forever (new API calls)
        # TODO: cache already found places
        venue_id = event_info['venue_id']
        if venue_id in all_venues:
            one_event['place'] = all_venues[venue_id]
        else:
            loc_resp = session.get(
                base_endpoint + '/venues/' + venue_id,
                headers = sample_headers,
                verify = True,
            )
            loc_info = loc_resp.json()
            new_place = {}
            loc_details = loc_info['address']
            new_place['location'] = {
                'latitude': float(loc_details['latitude']),
                'longitude': float(loc_details['longitude']),
                'street': loc_details['address_1'],
                'city': 'Los Angeles',
                'state': 'CA',
                'zipcode': loc_details['postal_code'],
                'country': 'United States'
            }
            new_place['name'] = loc_info['name']
            new_place['id'] = venue_id

            all_venues[venue_id] = new_place
            one_event['place'] = new_place

        cleaned_events.append(one_event)

    cleaned_events = categorizeEvents(cleaned_events)

    # autocategorization has a cleaner way to do this path switching
    savedPath = os.getcwd()
    os.chdir(API_UTILS_PATH)
    with open('evebr.json', 'w') as f:
        json.dump(cleaned_events, f, sort_keys=True, indent=4, separators=(',', ': '))
    os.chdir(savedPath)

    events_current_processed_collection.delete_many({})
    events_current_processed_collection.insert_many(cleaned_events)
    return len(cleaned_events)
    # if not all_events:
    #     print(response.json())
    # else:
    #     pprint(all_events[:3])
    #     print('# EVENTS: ' + str(len(all_events)))

if __name__ == '__main__':
    entire_eventbrite_retrieval(0)
