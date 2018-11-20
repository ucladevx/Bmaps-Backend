import requests
from fuzzywuzzy import fuzz
import random

url = 'http://api.mappening.io:5000/api/v2/locations/'
def fetch_locations():
	response = requests.get(url)
	data = response.json()
	locations = data['locations']
	names = []
	for location in locations:
		names.append(location['location']['location']['name'])
	return names

def test_swap(locations, iterations):
	for i in range(iterations):
		index = random.randint(0, len(locations))
		name = locations[index]
		original = name
		while True:
			char_index = random.randint(0, len(name) - 1)
			if (name[char_index] != ' '):
				break
		del locations[index]
		name = list(name)
		name[char_index] = name[len(name) - 1 - char_index]
		name = ''.join(name)
		print(original)
		print(name)
		print(fuzz.ratio(original, name))

def test_case(locations, iterations):
	for i in range(iterations):
		index = random.randint(0, len(locations))
		name = locations[index]
		original = name
		del locations[index]
		name = name.lower()
		print(original)
		print(name)
		print(fuzz.ratio(original, name))
		name = name.upper()
		print(original)
		print(name)
		print(fuzz.ratio(original, name))

if __name__ == '__main__':
	locations = fetch_locations()
	test_swap(locations, 5)	
	test_case(locations, 5)
