import nltk
nltk.download('stopwords')
nltk.download('perluniprops')
nltk.download('nonbreaking_prefixes')
nltk.download('punkt')

from ourDb import events_collection, total_events_collection, events_ml_collection
import re
import nltk
import string
from tqdm import tqdm
import numpy as np
from nltk.tokenize.moses import MosesTokenizer
from collections import Counter


from gensim.models import Phrases
from nltk.corpus import wordnet as wn

class PreprocessText:
    def __init__(self, categorizedEvents):
        """categorizedEvents should be a list of dictionaries each corresponding to an event
            X is the tokenized preprocessed text
            Y is the corresponding categories
            phraseMl is the phrase model that can further trained and used
            phrases is a list of all the phrases identified"""
        self.X = []
        self.Y = []
        tokenizer = MosesTokenizer() #tokenizers are basically an advanced split
        for e in categorizedEvents:
            text = e[u'name'] + " " + e[u'description']
            text = tokenizer.tokenize(text)
            text = self.preprocess(text)
            self.X.append(text)
            self.Y.append(e[u'category'])
        self.phraseMl = Phrases(self.X, min_count=3) #learn ml model for phrase
        self.X = list(self.phraseMl[self.X]) #use ml model for phrases
#         self.X = list(self.phraseMl[self.X]) #get triples
        self.phrases = phrases = set([w for doc in self.X for w in doc if '_' in w])
        
    def matchNotX(self, strg, search=re.compile(r'[^!#$%&()*+,-./:;<=>?@\\^_}|{~0123456789]').search):
        """make sure word has something than punctuation"""
        return bool(search(strg)) #make sure word has something other than punctuation

    def preprocess(self, text):
        """Remove all useless words and punct, make lowercase"""
        stoplist = set('for a of the and to in . / '.split())
        stoplist = set(nltk.corpus.stopwords.words('english')) | stoplist | set(string.punctuation)
        return [word.strip(string.punctuation).lower() for word in text if word not in stoplist and self.matchNotX(word)]    
        
    def topBigrams(self, texts, n, tri=False):
        """Other method of getting phrases, currently unused because phrases can be further trained(online) and saved"""
        flatTexts = []
        for text in texts:
            for word in text:
                flatTexts.append(word)
        bigram_measures = nltk.collocations.BigramAssocMeasures()
        trigram_measures = nltk.collocations.TrigramAssocMeasures()
        topAnswers = []
        if tri:
            finder = nltk.collocations.TrigramCollocationFinder.from_words(flatTexts)
            finder.apply_freq_filter(7)
            return finder.nbest(trigram_measures.pmi, n)
        else:
            finder = nltk.collocations.BigramCollocationFinder.from_words(flatTexts)
            finder.apply_freq_filter(7)
            return finder.nbest(bigram_measures.pmi, n)

def gatherCategorizedEvents():
    allCategorizedEvents = []
    allEvents = events_ml_collection.find({}, {"category": 1, "description": 1, "name": 1, "_id": 0})
    count = 0
    for e in allEvents:
        count += 1
        if 'category' in e and 'description' in e and 'name' in e:
            allCategorizedEvents.append(e)
    modernEvents = reduceCategories(allCategorizedEvents)
    print count, "total events, learning from the", len(modernEvents), "well categorized events"
    return modernEvents

############################################################################
########################### EVENT CATEGORIZATION ###########################
############################################################################

def someCurrentCategories():
    """Looks at current events for the categories list, to be used if Facebook changes its events in the future"""
    allCategorizedEvents = []
    allEvents = events_collection.find({}, {"category": 1, "description": 1, "name": 1, "_id": 0})
    for e in allEvents:
        if 'category' in e and 'description' in e and 'name' in e:
            allCategorizedEvents.append(e)
    skTarget = [e['category'] for e in allCategorizedEvents]
    count = sorted(list(set(skTarget)))
    print(count)
    
curListOfCategories = [u'ART', u'CAUSE', u'COMEDY_PERFORMANCE', u'DANCE', u'DRINKS', u'FILM', u'FITNESS', u'FOOD',
                       u'GAMES', u'GARDENING', u'HEALTH', u'LITERATURE', u'MEETUP', u'MUSIC', u'NETWORKING', u'PARTY',
                       u'RELIGION', u'SHOPPING', u'SPORTS', u'THEATER', u'WELLNESS']


def reduceCategories(events):
    """OTHER will be discarded from the training data"""
    categoryMapping = {
        u'BOOK': u'LITERATURE',
        u'COMEDY': u'COMEDY_PERFORMANCE',
        u'CLASS': u'OTHER',
        u'DINING': u'FOOD',
        u'FAMILY': u'OTHER',
        u'FESTIVAL': u'PARTY',
        u'FOOD_TASTING': u'FOOD',
        u'FUNDRAISER': u'CAUSE',
        u'LECTURE': u'OTHER',
        u'MOVIE': u'FILM',
        u'NEIGHBORHOOD': u'OTHER',
        u'NIGHTLIFE': u'OTHER',
        u'RELIGIOUS': u'RELIGION',
        u'VOLUNTEERING': u'CAUSE',
        u'WORKSHOP': u'OTHER'
    }
    
    for e in events:
        category = e['category']
        if category in categoryMapping:
            e['category'] = categoryMapping[category]
    reducedEvents = [e for e in events if e['category'] != u'OTHER']
    return reducedEvents


X = gatherCategorizedEvents()
skText = [e['name']+' '+e['description'] for e in X]
skTarget = [e['category'] for e in X]


############################################################################
############################ ML HELPER FUNCTIONS ###########################
############################################################################

from sklearn.cross_validation import train_test_split

def train(classifier, X, y, trails=25):
    scores = np.zeros(trails)
    for i in tqdm(range(0, trails)):
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=i)

        classifier.fit(X_train, y_train)
        scores[i] = (classifier.score(X_test, y_test))
    print "Average Accuracy over %d trials: %s" % (trails, np.mean(scores))
    classifier.fit(X, y)
    return classifier

def predictList(vectorizer, classifier, x):
    print(x)
    x = vectorizer.transform(x)
    y_pred = classifier.predict(x)
    print(y_pred)

def giveProbPerCategory(vectorizer, classifier, x, threshold=.15):
    print(x)
    x = vectorizer.transform(x)
    y_pred = classifier.predict_proba(x)

    strongest_category = ''
    highest_match = 0
    above_threshold = []
    for i in range(len(classifier.classes_)):
        
        if y_pred[0][i] > highest_match:
            highest_match = y_pred[0][i]
            strongest_category = classifier.classes_[i]
            
        if y_pred[0][i] > threshold:
            above_threshold.append(classifier.classes_[i])
    
    if not above_threshold:
        return [strongest_category]
    else:
        return above_threshold



############################################################################
############################### BEST ML MODELING ###########################
############################################################################

from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.multiclass import OneVsRestClassifier

# create the transform
vectorizer = TfidfVectorizer(stop_words='english')

# tokenize and build vocab
X = vectorizer.fit_transform(skText)

# print(vectorizer.vocabulary_)
# print(vectorizer.idf_)

nbModel = OneVsRestClassifier(MultinomialNB(alpha=0.05))

#predicted
 
nbModel = train(nbModel, X, skTarget)
## AVG ACCURACY - 25 TRIALS: 0.72326055313 ## 