import requests
import time, datetime
from pprint import pprint
import json

 # Updated coordinates of Bruin Bear
CENTER_LATITUDE = 34.070966
CENTER_LONGITUDE = -118.445

days_back = 0
days_forward = 2
now = datetime.datetime.now()
past_bound = (now - datetime.timedelta(days=days_back)).strftime('%Y-%m-%dT%H:%M:%S')
future_bound = (now + datetime.timedelta(days=days_forward)).strftime('%Y-%m-%dT%H:%M:%S')

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
    'location.within': '1mi',
    'start_date.range_start': past_bound,
    'start_date.range_end': future_bound,
    'sort_by': 'best'
}
response = session.get(
    base_endpoint + events_search_ep,
    headers = sample_headers,
    verify = True,  # Verify SSL certificate
    params = search_args,
)

all_events = response.json().get('events')
with open('eveb.json', 'w') as f:
    json.dump(all_events, f, sort_keys=True, indent=4, separators=(',', ': '))

# if not all_events:
#     print(response.json())
# else:
#     pprint(all_events[:3])
#     print('# EVENTS: ' + str(len(all_events)))