import requests
# import json

session = requests.Session()

personal_token = 'WVLKNUTHJ72TDTDV6GUP'
base_endpoint = 'https://www.eventbriteapi.com/v3'
sample_headers = {
    'Authorization': 'Bearer ' + personal_token
}

events_search_ep = '/events/search'

response = session.get(
    base_endpoint + events_search_ep,
    headers = sample_headers,
    verify = True,  # Verify SSL certificate
)
print(response.json()['events'][0]['name']['text'])