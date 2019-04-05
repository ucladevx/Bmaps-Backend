from fuzzywuzzy import fuzz
from abbreviations_map import abbreviations_map
import random
import re
import sys
import requests
# from mappening.utils.database import locations_collection
from unidecode import unidecode

def get_location_data_from_name(name, locations_map, all_locations):
	index = locations_map[name]
	return all_locations[index]
	

def match_location(target, threshold=65):
	target = unidecode(target.lower())
	cursor = locations_collection.find({}, {'_id': False})
	all_locations = [name for name in cursor]
	locations = [unidecode(name['location']['name']).lower() for name in all_locations]
	locations_map = {key: value for value, key in enumerate(locations)}
	name_from_abbreviation = None
	for key, value in abbreviations_map.items():
		for val in value:
			if target == val:
				name_from_abbreviation = key
				break
	
	if name_from_abbreviation:
		return get_location_data_from_name(name_from_abbreviation, locations_map, all_locations)

	best_score = -1
	best_location = ""
	best_index = -1
	for index, location in enumerate(locations):
		score = fuzz.token_set_ratio(target, location)
		if score > best_score:
			best_score = score
			best_location = location
			best_index = index

	if best_score > threshold:
		return all_locations[best_index]
	return None

def test(target, locations, locations_map, all_locations, threshold=65):
	target = unidecode(target.lower())
	best_score = -1
	best_location = ""
	best_index = -1
	
	name_from_abbreviation = None
	for key, value in abbreviations_map.items():
		for val in value:
			if target == val:
				name_from_abbreviation = key
				break

	if name_from_abbreviation:
		return get_location_data_from_name(name_from_abbreviation, locations_map, all_locations)

	for index, location in enumerate(locations):
		score = fuzz.token_set_ratio(target, location)
		if score > best_score:
			best_score = score
			best_location = location
			best_index = index

	print("best score {0}: {1}".format(best_score, locations[best_index]))
	return all_locations[best_index]

def test_top(target, locations, locations_map, all_locations, num=5):
	scored_locs = []
	target = unidecode(target.lower())

	name_from_abbreviation = None
	for key, value in abbreviations_map.items():
		for val in value:
			if target == val:
				name_from_abbreviation = key
				break

	if name_from_abbreviation:
		return get_location_data_from_name(name_from_abbreviation, locations_map, all_locations)

	for location in locations:		
		score = fuzz.token_set_ratio(target, location)
		scored_locs.append(tuple((location,score)))

	sorted_locs = sorted(scored_locs, key=lambda tup: tup[1], reverse=True)

	print(sorted_locs[:num])
	return sorted_locs

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

def main():
	if len(sys.argv) != 2:
		raise(ValueError("Script requires a single location to match"))
	target = sys.argv[1]
	response = requests.get("http://localhost:5000/api/v2/locations")
	data = response.json()
	data = data['locations']
	all_locations = [unidecode(location['location']['location']['name'].lower()) for location in data]
	locations_map = {key: value for value, key in enumerate(all_locations)}
	print(test(target, all_locations, locations_map, data))
	test_top(target, all_locations, locations_map, data)

if __name__ == '__main__':
	main()
