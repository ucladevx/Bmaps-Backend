import requests
from fuzzywuzzy import fuzz
from allLocations import abbreviations_map
import random
import re
import sys

print(abbreviations_map)

url = 'http://api.mappening.io:5000/api/v2/locations/'
def fetch_locations():
	response = requests.get(url)
	data = response.json()
	locations = data['locations']
	names = []
	for location in locations:
		names.append(location['location']['location']['name'])
	print('...finished fetching all locations!')
	return names

def swap(string):
	string = list(string)
	index1 = random.randint(0, len(string) - 1)
	index2 = None
	while (True):
		index2 = random.randint(0, len(string) - 1)
		if index2 != index1:
			break
	
	string[index1] = string[index2]
	return ''.join(string)

def test_swap(locations, iterations):
	for i in range(iterations):
		index = random.randint(0, len(locations))
		name = locations[index]
		original = name
		del locations[index]
		name = swap(name)
		print(original)
		print(name)
		print(fuzz.ratio(original, name))

def test_case(locations, iterations): #very low accuracy, should convert locations to lower case before trying to match
	for i in range(iterations):
		index = random.randint(0, len(locations) - 1)
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

def find_match_with_highest_accuracy(locations, iterations):
	correct = 0
	for i in range(iterations):
		index = random.randint(0, len(locations) - 1)
		location = locations[index]
		original = location
		for i in range(4):
			location = swap(location)
		location = location.lower()
		highest_score = -1
		best = None
		for name in locations:
			name = name.lower()
			score = fuzz.ratio(name, location)
			if score >= highest_score:
				highest_score = score
				best = name
		print('actual: ' + original)
		print(location)
		print('best: ' + best)
		if best.lower() == original.lower():
			correct += 1
		print(highest_score)
		print('\n')
	return correct

def print_all_locations(locations):
	print(*locations, sep='\n')

if __name__ == '__main__':
	locations = fetch_locations()
	locations = sorted(locations)
	# print_all_locations(locations)
	iterations = int(sys.argv[1])
	# print('==========================================================')
	# test_swap(locations, 5)	
	# print('==========================================================')
	# test_case(locations, 5)
	# print('==========================================================')
	correct = find_match_with_highest_accuracy(locations, iterations)
	print('Accuracy: {}'.format(correct/iterations))
