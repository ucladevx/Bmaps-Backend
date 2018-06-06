import cPickle as pickle
import pandas as pd
from scipy.sparse import hstack
import itertools

#Run this file to grom events_current_collection and make events_current_processed_collection, delete old events_current_processed_collection first
# Needed to get access to mappening.utils.database when running just this file since this is under mappening.ml
import sys
sys.path.insert(0,'./../..')

from mappening.utils.database import events_db, events_current_collection

def labelFreeFood(events):
    """
    :param X: should be list of dictionary elements
    Returns list of events updated with a list of categories
    """

    #ensure there is a name and description for machine learning
    for event in events:
        if 'name' not in event:
            event['name'] = ''
        if 'description' not in event:
            event['description'] = ''

    # Load data
    X = pd.DataFrame(events)
    with open(r"foodModel.pickle", "r") as model:
        classifier = pickle.load(model)
    with open(r"nameFoodVectorizer.pickle", "r") as model:
        nameVectorizer = pickle.load(model)
    with open(r"detailFoodVectorizer.pickle", "r") as model:
        detailVectorizer = pickle.load(model)

    X_name_transform = nameVectorizer.transform(X['name'])
    X_details_transform = detailVectorizer.transform(X['description'])
    X_total_transform = hstack([X_name_transform, X_details_transform])
    y_pred = classifier.predict(X_total_transform)

    for i, event in enumerate(events):
        event['free_food'] = y_pred[i]

    #UNDO initial empty desctiption and name adds and base category
    if 'category' in event:
        del event['category']
    if event['name'] == '':
        del event['name']
    if event['description'] == '':
        del event['description']

    return events

def labelFoodAllCurrentEvents():
    """
    :Description: Takes all the events in events_current_collection and creates new events_current_processed_collection
        with all events having a list of categories now
    """
    events_current_processed_collection = events_db.events_current_processed_food
    allEvents = [e for e in events_current_collection.find()]
    allEvents = categorizeEvents(allEvents)
    events_current_processed_collection.insert_many(allEvents)
    print("Created new categorized event collection: events_current_processed")

if __name__ == "__main__":
    labelFoodAllCurrentEvents()
