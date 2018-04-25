import requests
from pprint import pprint
# import json

 # Updated coordinates of Bruin Bear
CENTER_LATITUDE = 34.070966
CENTER_LONGITUDE = -118.445

session = requests.Session()

personal_token = 'WVLKNUTHJ72TDTDV6GUP'
base_endpoint = 'https://www.eventbriteapi.com/v3'
sample_headers = {
    'Authorization': 'Bearer ' + personal_token
}

events_search_ep = '/events/search'
search_args = {
    'location.latitude': str(CENTER_LATITUDE),
    'location.longitude': str(CENTER_LONGITUDE),
    'location.within': '2mi'
}

response = session.get(
    base_endpoint + events_search_ep,
    headers = sample_headers,
    verify = True,  # Verify SSL certificate
)
pprint(response.json()['events'][:3])