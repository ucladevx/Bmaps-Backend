from flask import Flask, jsonify, request, json, Blueprint
from flask_cors import CORS, cross_origin

import nltk
nltk.download('perluniprops')
nltk.download('nonbreaking_prefixes')
nltk.download('stopwords')
nltk.download('punkt')

import re
import string
from tqdm import tqdm
from nltk.tokenize.moses import MosesTokenizer

from nltk.corpus import wordnet as wn

Process = Blueprint('Process', __name__)

# Enable Cross Origin Resource Sharing (CORS)
cors = CORS(Process)

@Process.route('/api/process', methods=['GET'])
def processText():
    tokenizer = MosesTokenizer() #tokenizers are basically an advanced split

    text = "testing this. UCLA ackerman for Boelter 3400 why engr 4 at UCLA. Rstaurat of Los Angeles LA, Room 4760 @ the place - UCLA"
    text = tokenizer.tokenize(text)
    text = preprocess(text)
    return jsonify(text)

# [
#   "testing", 
#   "ackerman", 
#   "boelter", 
#   "engr", 
#   "rstaurat", 
#   "place"
# ]

def matchNotX(strg, search=re.compile(r'[^!#$%&()*+,-./:;<=>?@\\^_}|{~0123456789]').search):
    """make sure word has something than punctuation"""
    return bool(search(strg)) #make sure word has something other than punctuation

def preprocess(text):
    """Remove all useless words and punct, make lowercase"""
    stoplist = set('for a of the and to in . / UCLA Westwood LA Los Angeles Room The @ at - ,'.split())
    stoplist = set(nltk.corpus.stopwords.words('english')) | stoplist | set(string.punctuation)
    return [word.strip(string.punctuation).lower() for word in text if word not in stoplist and matchNotX(word)]    
