from mappening.utils.database import events_current_processed_collection
from mappening.ml.autocategorization import categorizeEvents
from mappening.ml.autofood import labelFreeFood
from mappening.utils.secrets import EVENTBRITE_USER_KEY

import os
import sys
import time, datetime
from pprint import pprint
from tqdm import tqdm
import json
import requests

from definitions import API_UTILS_PATH

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

# Process for frontend to use it 
def process_events(all_events):
    all_venues = {}
    cleaned_events = []
    session = requests.Session()

    personal_token = EVENTBRITE_USER_KEY
    base_endpoint = 'https://www.eventbriteapi.com/v3'
    sample_headers = {
        'Authorization': 'Bearer ' + personal_token
    }
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

    # TODO: hangs on pickle.load(model)
    categorized_clean_events = categorizeEvents(cleaned_events)
    categorized_clean_events = labelFreeFood(categorized_clean_events)

    # Autocategorization has a cleaner way to do this path switching
    savedPath = os.getcwd()
    os.chdir(API_UTILS_PATH)
    with open('evebr.json', 'w') as f:
        json.dump(categorized_clean_events, f, sort_keys=True, indent=4, separators=(',', ': '))
    os.chdir(savedPath)

    events_current_processed_collection.delete_many({})
    events_current_processed_collection.insert_many(categorized_clean_events)
    return len(categorized_clean_events)
    # if not all_events:
    #     print(response.json())
    # else:
    #     pprint(all_events[:3])
    #     print('# EVENTS: ' + str(len(all_events)))
    print('Finished processing Eventbrite events!')
