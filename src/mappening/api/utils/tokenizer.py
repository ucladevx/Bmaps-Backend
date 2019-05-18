import nltk
nltk.download('perluniprops')
nltk.download('nonbreaking_prefixes')
nltk.download('stopwords')
nltk.download('punkt')

from nltk.tokenize.moses import MosesTokenizer, MosesDetokenizer
import string
import re

def tokenize_text(text):
    # Tokenizers are basically an advanced split
    tokenizer = MosesTokenizer()
    detokenizer = MosesDetokenizer()

    processed_text = tokenizer.tokenize(text)

    # Need to detokenize to get all the weird symbols back as symbols
    processed_text = detokenizer.detokenize(processed_text)

    processed_text = preprocess(processed_text)

    return " ".join(processed_text) 
    # return jsonify(processed_text)

# Checks that word has something other than punctuation
def matchNotX(strg, search=re.compile(r'[^!#$%&()*+,-./:;<=>?@\\^_}|{~0123456789]').search):
    return bool(search(strg)) 

# Remove all useless words and punctuation, make lowercase
# TODO: Add words here to filter them out
def preprocess(text):
    stoplist = set('for a of the and to in . / center field plaza residential los ucla angeles la westwood room dormitory dorm building bldg ofc office hall the & @ at - ,'.split())
    stoplist = set(nltk.corpus.stopwords.words('english')) | stoplist | set(string.punctuation)
    return [word.strip(string.punctuation).lower() for word in text if word.lower() not in stoplist and matchNotX(word)]    
