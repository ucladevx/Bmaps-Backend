from fuzzywuzzy import fuzz
from all_locations import abbreviations_map
import random
import re
import sys
from mappening.utils.database import locations_collection
from unidecode import unidecode


def match_location(target, threshold=0.65):
	target = unidecode(target.lower())
	cursor = locations_collection.find({}, {'_id': False})
	all_locations = [name for name in cursor]
	locations = [unidecode(name['location']['name']).lower() for name in all_locations]

	best_score = -1
	best_location = ""
	best_index = -1
	for index, location in enumerate(locations):
		score = fuzz.ratio(target, location)
		if score > best_score:
			best_score = score
			best_location = location
			best_index = index

	print("best score {}".format(best_score))
	print(all_locations[best_index])
	if best_score > threshold:
		return all_locations[best_index]
	return None


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
