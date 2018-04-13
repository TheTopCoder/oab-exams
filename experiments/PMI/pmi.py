#!/usr/bin/python3

### from: http://www.aclweb.org/anthology/P89-1010.pdf
# How to calculate PMI:

# What is "mutual information"? According to [Fano (1961), p. 28], if
# two points (words), x and y, have probabilities P(x) and P(y), then
# their mutual information, I(x,y), is defined to be

# I(x,y) = log2 (P(x,y) / (P(x) P(y)))

# Informally, mutual information compares the probability of observing
# x and y together (the joint probability) with the probabilities of
# observing x and y independently (chance). If there is a genuine
# association between x and y, then the joint probability P(x,y) will be
# much larger than chance P(x) P(y), and consequently I(x,y) >> 0. If
# there is no interesting relationship between x and y, then P(x,y) ~
# P(x) P(y), and thus, I(x,y) ~ 0. If x and y are in complementary
# distribution, then P(x,y) will be much less than P(x) P(y), forcing
# I(x,y) << O.

# In our application, word probabilities, P(x) and P(y), are estimated
# by counting the number of observations of x and y in a corpus, f(x)
# and f(y), and normalizing by N, the size of the corpus. (Our
# examples use a number of different corpora with different sizes: 15
# million words for the 1987 AP corpus, 36 million words for the 1988
# AP corpus, and 8.6 million tokens for the tagged corpus.) Joint
# probabilities, P(x,y), are estimated by counting the number of times
# that x is followed by y in a window of w words fw(x,y), and
# normalizing by N.

# The window size parameter allows us to look at different
# scales. Smaller window sizes will identify fixed expressions
# (idioms) and other relations that hold over short ranges; larger
# window sizes will highlight semantic concepts and other
# relationships that hold over larger scales. For the remainder of
# this paper, the window size, w, will be set to 5 words as a
# compromise; thissettingislargeenough to show some of the constraints
# between verbs and arguments, but not so large that it would wash out
# constraints that make use of strict adjacency.

### from: https://www.aaai.org/ocs/index.php/AAAI/AAAI16/paper/view/11963

# The PMI solver formalizes a way of computing and applying such
# associational knowledge. Given a question q and an answer option ai,
# it uses pointwise mutual information (Church and Hanks 1989) to
# measure the strength of the associations between parts of q and
# parts of ai. Given a large corpus C, PMI for two n-grams x and y is
# defined as:

# PMI (x, y) = log p(x, y) p(x)p(y)

# Here p(x, y) is the joint probability that x and y occur together in
# the corpus C, within a certain window of text (we use a 10 word
# window). The term p(x)p(y), on the other hand, represents the
# probability with which x and y would occur together if they were
# statistically independent. The ratio of p(x, y) to p(x)p(y) is thus
# the ratio of the observed co-occurrence to the expected
# co-occurrence. The larger this ratio, the stronger the association
# between x and y.

# We extract unigrams, bigrams, trigrams, and skip-bigrams from the
# question q and each answer option ai. We use the SMART stop word
# list (Salton 1971) to filter the extracted n-grams, but allow
# trigrams to have a stop word as their middle word. The answer with
# the largest average PMI, calculated over all pairs of question
# n-grams and answer option n-grams, is the best guess for the PMI
# solver.

import nltk
import os, argparse, json, re, math, statistics, sys

from multiprocessing import Pool

# need to remove stopwords
def split(s, stopwords=None):
    split = [ x.lower() for x in re.sub(r'\W+', ' ', s).split() ]
    if stopwords:
        sw_set = set(stopwords)
        return [ x for x in split if x not in sw_set ]
    return split

def count_occurrences(x, corpus):
    "Count occurrences of n-gram X in CORPUS."
    total_words = 0
    total_occurrences = 0
    for (sentence,sentence_len) in corpus:
        total_occurrences += sentence.count(x)
        total_words = sentence_len
        
    return total_occurrences / total_words

def count_co_occurrences(x,y, corpus):
    x_y = " ".join([x,y])
    return count_occurrences(x_y, corpus)
    
def pmi(x_,y_,corpus):
    """Compute PMI of X and Y in CORPUS; here X and Y are strings
representing n-grams (each gram separated by space) and CORPUS is an
array of strings.  For this experiment we are considering the window
size the extension of each string."""
    x = " ".join(x_)
    y = " ".join(y_)
    px = count_occurrences(x, corpus)
    py = count_occurrences(y, corpus)
    pxy = count_co_occurrences(x, y, corpus)
    if pxy == 0:
        return 0
    return math.log( pxy / (px*py), 2)

def load_stopwords():
    sw = []
    sw_file = ""
    if os.path.isfile('../stopwords-pt.txt'):
        sw_file = '../stopwords-pt.txt'
    else:
        sw_file = 'stopwords-pt.txt'
    with open(sw_file, 'r') as f:
        for l in f:
            sw.append(l.strip())
    return set(sw)

def load_oab(es):
    doc = { 'size' : 5000, 'query': {'match_all' : {} } }
    
    res = es.search(index="oab", doc_type='doc', body=doc)
    
    oab = []
    
    for r in res['hits']['hits']:
        oab.append(r['_source'])

    return oab

def load_corpus(es):
    doc = { 'size' : 5000, 'query': {'match_all' : {} } }

    corpus = []
    res = es.search(index="corpus", doc_type="sentence", body=doc)
    
    for r in res['hits']['hits']:
        corpus.append(r['_source'])

    return corpus

def unigram(text, sw):
    return list(nltk.ngrams(split(text, sw), 1))
def bigram(text, sw):
    return list(nltk.ngrams(split(text, sw), 2))
def trigram(text, sw):
    return list(nltk.ngrams(split(text, sw), 3))
def skip_trigram(text, sw):
    return list([ (x[0],x[2]) for x in nltk.ngrams(split(text, sw), 3) ])

def compute_all_pmi(ngram_fn, oab, corpus, sw):
    for q in oab:
        enum = ngram_fn(q['enum'], sw)

        for o in q['options']:
            option_text = ngram_fn(o['text'], sw)

            sum = 0
            len = 0

            for x, y in [(x,y) for x in enum for y in option_text]:
                sum += pmi(x,y,corpus)
                len += 1

            avg = 0
            if len == 0:
                print(ngram_fn, o)
            else:
                avg = sum/len
                
            if 'pmi' in o:
                o['pmi'].append(avg)
            else:
                o['pmi'] = [avg]

def compute_q_pmi(ngram_fn, q, corpus, sw):
    enum = ngram_fn(q['enum'], sw)

    for o in q['options']:
        option_text = ngram_fn(o['text'], sw)

        sum = 0
        len = 0

        for x, y in [(x,y) for x in enum for y in option_text]:
            sum += pmi(x,y,corpus)
            len += 1

        avg = 0
        if len == 0:
            print(ngram_fn, o)
        else:
            avg = sum/len

        if 'pmi' in o:
            o['pmi'].append(avg)
        else:
            o['pmi'] = [avg]

def main():

    oab = []
    corpus = []
    sw = load_stopwords()
    
    with open(sys.argv[1],'r') as f:
        oab = json.load(f)
    with open('corpus.json','r') as f:
        corpus = json.load(f)

    preprocessed_corpus = []
    for raw in corpus:
        split_sentence = split(raw['text'], sw)
        preprocessed_corpus.append((' '.join(split_sentence), len(split_sentence)))

    for ngram_fn in [unigram, bigram, trigram, skip_trigram]:
        compute_all_pmi(ngram_fn, oab, preprocessed_corpus, sw)

    with open('pmi' + sys.argv[1],'w') as f:
        json.dump(oab, f)

if __name__ == "__main__":
    main()