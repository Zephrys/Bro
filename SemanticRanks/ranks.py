# -*- coding: UTF-8 -*-
from __future__ import division
import nltk
from nltk.tag.perceptron import PerceptronTagger
from nltk.corpus import stopwords
import enchant
from nltk.corpus import wordnet as wn
from nltk.corpus import sentiwordnet as swn
from pymongo import MongoClient
import inflect

p = inflect.engine()
stop = stopwords.words('english')


eng_check = enchant.Dict("en_US")

tagger = PerceptronTagger()
tagset = None

client = MongoClient('mongodb://localhost:27017/')
db = client.Bro
reviews_db = db.tripadvisor_reviews
place_db = db.tripadvisor_places
result_db = db.tripadvisor_results


def strip_proppers_POS(text, search):
    text = text.decode('utf-8', 'ignore')
    tokens = nltk.word_tokenize(text.lower())
    tagged = nltk.tag._pos_tag(tokens, tagset, tagger)
    res = []

    search_index = [i for i, val in enumerate(tokens)
                    if (p.singular_noun(val) == search or
                    (not p.singular_noun(val) and val == search))
                    ]

    words = [(word, pos) for word, pos in tagged if (pos[0] == "J") and
             len(word) > 2 and
             word not in stop and
             not p.singular_noun(word) and
             eng_check.check(word) and
             not any(ccc.isdigit() for ccc in word)]

    adj_count = 0
    for a in range(0, len(tagged)):
        if tagged[a] in words:
            if tagged[a][1][0] == "J":
                adj = tagged[a][0]
                dist = min([abs(a-s) for s in search_index])
                score = 0
                adj_synset = swn.senti_synsets(adj, 'a')
                if len(adj_synset) <= 0:
                    adj_synset = swn.senti_synsets(adj, 'v')
                if len(adj_synset) <= 0:
                    synonyms = []
                    for ss in wn.synsets(adj):
                        for j in ss.lemma_names():
                            synonyms.append(j)
                    if len(synonyms) > 1:
                        synonym_count = 0
                        for s in range(0, len(synonyms)):
                            if synonym_count < 2 and synonyms[s] != adj:
                                w1 = synonyms[s]
                                adj_synset1 = swn.senti_synsets(w1, 'a')
                                if len(adj_synset1) > 0:
                                    score += adj_synset1[0].pos_score()\
                                        - adj_synset1[0].neg_score()
                                    synonym_count += 1
                        score = score/2
                else:
                    score = adj_synset[0].pos_score() \
                        - adj_synset[0].neg_score()
                try:
                    res.append((adj, score/(pow(dist, 2))))
                    adj_count += 1
                except:
                    pass
    return (res, adj_count)


def get_reviews(search, location):
    arr = reviews_db.find_one({'keyword': search.lower(), 'place': location.lower()})
    places = [arr['results'][i] for i in arr['results']]
    return places


def accumulate(search_query, location):

    places = get_reviews(search_query, location)
    print len(places)
    res = []

    for place in places:
        reviews = place['reviews']
        place_rating = place['rating']

        if place_rating[1] == ' ':
            place_rating = float(place_rating[0:1])/5
        else:
            place_rating = float(place_rating[0:3])/5

        score_place = 0

        for r in reviews:
            review_text = r['review'].encode('utf-8', 'ignore')

            score_review = 0

            for search in nltk.word_tokenize(search_query.lower()):

                if p.singular_noun(search):
                    search = p.singular_noun(search)
                try:
                    review_adjectives = strip_proppers_POS(review_text,
                                                           search)[0]
                    adj_count = strip_proppers_POS(review_text, search)[1]

                    for i in review_adjectives:
                        score_review += i[1]

                    score_review = score_review/adj_count
                except:
                    continue

            score_place += score_review

        res.append({'place_url': place['url'],
                    'score':  score_place * place_rating/len(reviews)})

    return res


def integrated(search_query, location, desired_sentiment=1):
    result_places = accumulate(search_query, location)
    sorted_places = sorted(result_places,
                           key=lambda x: x['score'], reverse=True)
    res = {}
    res['search'] = search_query
    res['location'] = location
    res['desired_sentiment'] = desired_sentiment

    if desired_sentiment == 1:
        res_url = sorted_places[0]['place_url']
    elif desired_sentiment == 0:
        res_url = sorted_places[-1]['place_url']

    res['url'] = res_url
    result_db.insert_one(res)
    return res_url
