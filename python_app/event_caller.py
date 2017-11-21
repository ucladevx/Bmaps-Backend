import requests
import json
from pprint import pprint

# Got APP_ID and APP_SECRET from Mappening app with developers.facebook.com
FACEBOOK_APP_ID = '789442111228959'
FACEBOOK_APP_SECRET = '6ec0e473acf4d91b4ea3346b75e05268'
ACCESS_TOKEN_URL = 'https://graph.facebook.com/oauth/access_token'

SEARCH_URL = 'https://graph.facebook.com/search'
# coordinates of Bruin Bear
CENTER_LATITUDE = 34.070966
CENTER_LONGITUDE = -118.445
SEARCH_TERMS = ['ucla', 'bruin', 'ucla theta', 'ucla kappa']
UCLA_ZIP_STRINGS = ['90024', '90095']

s = requests.Session()

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
def page_in_right_location(page_loc_data):
    if 'zip' in page_loc_data:
        zip_string = page_loc_data['zip'][:5]
        if zip_string in UCLA_ZIP_STRINGS:
            return True
    elif 'city' in page_loc_data and 'state' in page_loc_data:
        if page_loc_data['city'] == 'Los Angeles' and page_loc_data['state'] == 'CA':
            return True
    return False

# for searching both place and page
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
            if 'location' not in page or page_in_right_location(page['location']):
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
            elif page_in_right_location(place['location']):
                ucla_entities[place['id']] = place['name']
        
        # check if there is a next page of results
        if 'paging' not in responses or 'next' not in responses['paging']:
            break
        else:
            curr_url = responses['paging']['next']
        page_num += 1

    return ucla_entities

def get_events_from_pages(pages_by_id, app_access_token):
    return []

def get_facebook_events():
    APP_ACCESS_TOKEN = get_app_token()
    # print(APP_ACCESS_TOKEN)
    
    # search for UCLA-associated places and groups
    # limit to as high as possible, go until no pages left
    # type = places: give center coordinates (of Bruin Bear), distance 1000 (in meters), limit max 100
    # type = pages: search with reserved terms, limit = 1000, check location as well
    # 2 types of places: ones with events, ones without, cannot do anything about without events
    # pre-filtering: only store places / pages with UCLA zip code, or LA CA, or no place at all (filter events later)
    pages_by_id = find_ucla_entities(APP_ACCESS_TOKEN)
    with open('pages.json', 'w') as file:
        json.dump(pages_by_id, file, sort_keys=True, indent=4, separators=(',', ': '))
    # pprint(pages_by_id)
    return {'End message': 'Success!'}
    

if __name__ == '__main__':
    get_facebook_events()