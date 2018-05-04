import cPickle as pickle
import pandas as pd
from scipy.sparse import hstack

# Needed to get access to mappening.utils.database when running just this file since this is under mappening.ml
import sys
sys.path.insert(0,'./../..')

from mappening.utils.database import events_db, events_current_collection

LIST_OF_CATEGORIES = [u'ART', u'CAUSE', u'COMEDY_PERFORMANCE', u'DANCE', u'DRINKS', u'FILM', u'FITNESS', u'FOOD',
                   u'GAMES', u'GARDENING', u'HEALTH', u'LITERATURE', u'MEETUP', u'MUSIC', u'NETWORKING', u'PARTY',
                   u'RELIGION', u'SHOPPING', u'SPORTS', u'THEATER', u'WELLNESS']

def categorizeEvents(events, threshold=.1):
    """
    :param X: should be list of dictionary elements
    Returns list of events updated with a list of categories
    """

    #make copy just for machine learning
    #TODO: could be optimized by just changing the original events then running through and deleting empty string values
    X = events[:]
    for event in X:
        if 'name' not in event:
            event['name'] = ''
        if 'description' not in event:
            event['description'] = ''

    # Load data
    X = pd.DataFrame(events)
    with open(r"categorizationModel.pickle", "r") as model:
        rf = pickle.load(model)
    with open(r"nameVectorizer.pickle", "r") as model:
        nameVectorizer = pickle.load(model)
    with open(r"detailVectorizer.pickle", "r") as model:
        detailVectorizer = pickle.load(model)

    catLists = predictCategories(nameVectorizer, detailVectorizer, rf, X, threshold)

    ## basically if the event already has a category put that first and then ensure no duplicates
    for i in range(0, len(catLists)):
        curCategory = events[i].get('category', None)
        if curCategory not in LIST_OF_CATEGORIES:
            events[i]['category'] = catLists[i]
        else:
            events[i]['category'] = [curCategory]
            for cat in catLists[i]:
                if cat != curCategory:
                    events[i]['category'].append(cat)

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
    Takes all the events in events_current_collection and creates new events_curcategorized_collection
        with all events having a list of categories now
    """
    events_curcategorized_collection = events_db.events_curcategorized
    allEvents = [e for e in events_current_collection.find()]
    allEvents = categorizeEvents(allEvents)
    events_curcategorized_collection.insert_many(allEvents)

if __name__ == "__main__":
    categorizeAllCurrentEvents()
