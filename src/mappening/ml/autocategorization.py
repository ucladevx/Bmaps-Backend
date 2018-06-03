import cPickle as pickle
import pandas as pd
from scipy.sparse import hstack
import itertools

import os
# use this to change to this folder, since this might be run from anywhere in project...
from definitions import ML_PATH

# https://stackoverflow.com/questions/431684/how-do-i-change-directory-cd-in-python/13197763#13197763
# make a nice cd command that auto changes directory back when exited
class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

# Run this file to groom events_current_collection and make events_current_processed_collection, delete old events_current_processed_collection first
# Needed to get access to mappening.utils.database when running just this file since this is under mappening.ml
import sys
sys.path.insert(0,'./../..')

# TODO: use these DBs for categorizeAllCurrentEvents
from mappening.utils.database import events_fb_collection, events_eventbrite_collection
from mappening.utils.database import events_current_processed_collection

LIST_OF_CATEGORIES = [u'ART', u'CAUSE', u'COMEDY_PERFORMANCE', u'DANCE', u'DRINKS', u'FILM', u'FITNESS', u'FOOD',
                   u'GAMES', u'GARDENING', u'HEALTH', u'LITERATURE', u'MEETUP', u'MUSIC', u'NETWORKING', u'PARTY',
                   u'RELIGION', u'SHOPPING', u'SPORTS', u'THEATER', u'WELLNESS']

def categorizeEvents(events, threshold=.1):
    """
    :param X: should be list of dictionary elements
    Returns list of events updated with a list of categories
    """

    # ensure there is a name and description for machine learning
    for event in events:
        if 'name' not in event or not event['name']:
            event['name'] = ''
        if 'description' not in event or not event['description']:
            event['description'] = ''

    # Load data
    X = pd.DataFrame(events)
    # change path to load these files, for sure (correct directory)
    with cd(ML_PATH):
        with open(r"categorizationModel.pickle", "r") as model:
            rf = pickle.load(model)
        with open(r"nameVectorizer.pickle", "r") as model:
            nameVectorizer = pickle.load(model)
        with open(r"detailVectorizer.pickle", "r") as model:
            detailVectorizer = pickle.load(model)

    catLists = predictCategories(nameVectorizer, detailVectorizer, rf, X, threshold)

    # basically if the event already has a category put that first and then ensure no duplicates
    for (event, catList) in itertools.izip(events, catLists):
        curCategory = event.get('category', None)
        if curCategory not in LIST_OF_CATEGORIES:
            event['categories'] = catList
        else:
            event['categories'] = [curCategory]
            for cat in catList:
                if cat != curCategory:
                    event['categories'].append(cat)

        # UNDO initial empty desctiption and name adds and base category
        if 'category' in event:
            del event['category']
        if event['name'] == '':
            del event['name']
        if event['description'] == '':
            del event['description']

    return events

def predictCategories(nameVectorizer, detailVectorizer, classifier, X, threshold=.1):
    """
    :param nameVectorizer: TfidfVectorizer for the event names
    :param detailVectorizer: TfidfVectorizer for details
    :param classifer: scikit classifer with predict probability function(e.g RandomForestClassifier)
    :param X: pandas dataframe with 'name' and 'description' columns
    :param threshold: probabilty threshold for classifer prediction(note depending on classifer p varies)

    Returns parallel list of categories where the first elements have higher probability
    """

    X_name_transform = nameVectorizer.transform(X['name'])
    X_details_transform = detailVectorizer.transform(X['description'])
    X_total_transform = hstack([X_name_transform, X_details_transform])
    y_pred = classifier.predict_proba(X_total_transform)
    y_categories = []

    #create list of categories of len > 0 or more if over threshold
    for i in range(0, X_total_transform.shape[0]):
        current_categories_probabilities = [] #tuple of category name and prob

        #create tuple of category, class
        for j in range(0, len(classifier.classes_)):
            current_categories_probabilities.append((classifier.classes_[j], y_pred[i][j]))

        current_categories_probabilities.sort(key=lambda x: x[1], reverse=True) #put highest prob categories first
        current_categories = []
        for k, cp in enumerate(current_categories_probabilities):
            if k == 0 or cp[1] > threshold: #ensures at least one cat
                current_categories.append(cp[0])
        y_categories.append(current_categories)

    return y_categories

def categorizeAllCurrentEvents():
    """
    :Description: Takes all the events in ALL source DBs and puts in new events_current_processed_collection
        with all events having a list of categories now
    """
    # TODO: get events from multiple raw event DBs (imported above) instead of 1 events_current
    # since these include historical events, make sure event dates end after NOW

    # allEvents = [e for e in events_current_collection.find()]
    # allEvents = categorizeEvents(allEvents)
    # events_current_processed_collection.insert_many(allEvents)
    print("Added to categorized event collection: events_current_processed")

if __name__ == "__main__":
    categorizeAllCurrentEvents()
