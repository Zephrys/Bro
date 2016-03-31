# -*- coding: UTF-8 -*-
from __future__ import division
import nltk
from nltk.tag.perceptron import PerceptronTagger
from nltk.corpus import stopwords
from nltk.tag import pos_tag
import enchant
eng_check = enchant.Dict("en_US")
tagger = PerceptronTagger()
tagset = None
import inflect
p = inflect.engine()
stop = stopwords.words('english')

from nltk.corpus import wordnet as wn
from nltk.corpus import sentiwordnet as swn

from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client.Bro
reviews_db = db.tripadvisor
place_db = db.tripadvisor_places

def strip_proppers_POS(text, search):
	text = text.decode('utf-8', 'ignore')
	tokens = nltk.word_tokenize(text.lower())
	tagged = nltk.tag._pos_tag(tokens,tagset, tagger)
	res = []
	search_index = [i for i,val in enumerate(tokens) if ((p.singular_noun(val) and p.singular_noun(val)==search) or (not p.singular_noun(val) and val	==search))]
	words = [(word,pos) for word,pos in tagged if (pos[0]=="J") and len(word)>2 and word not in stop and not p.singular_noun(word) and eng_check.check(word) and not any(ccc.isdigit() for ccc in word)]

	for a in range(0,len(tagged)):
		if tagged[a] in words:		
			flag = 0
			if tagged[a][1][0] == "J":			
				adj = tagged[a][0]
				dist = min([abs(a-s) for s in search_index])
				score = 0
				neg_score = 0
				adj_synset = swn.senti_synsets(adj,'a')
				if len(adj_synset) <= 0:
					adj_synset = swn.senti_synsets(adj,'v')
				if len(adj_synset) <= 0:
					synonyms = []
					for ss in wn.synsets(adj):
						for j in ss.lemma_names():
							synonyms.append(j)
					if len(synonyms)>1:
						synonym_count = 0
						for s in range(0,len(synonyms)):
							if synonym_count < 2 and synonyms[s] != adj:
								w1 = synonyms[s]
								adj_synset1 = swn.senti_synsets(w1,'a')
								if len(adj_synset1)>0:
									score += adj_synset1[0].pos_score()
									neg_score += adj_synset1[0].pos_score()
									synonym_count += 1
						score=score/2
				else:
					score = adj_synset[0].pos_score()
					neg_score = adj_synset[0].neg_score()
				try:
					res.append((adj,score/(pow(dist,2)),neg_score/(pow(dist,2))))
				except:
					pass
	return res

def get_reviews(search, location):
	arr = reviews_db.find_one({'keyword':search,'place':location})
	places = [arr['results'][i] for i in arr['results']]
	return places

def accumulate(search_query, location):

	places = get_reviews(search_query,location)
	print len(places)
	res = []

	for place in places:	
		reviews = place['reviews']

		positive_score_place = 0
		negative_score_place = 0
			
		for r in reviews:
			review_text = r['review'].encode('utf-8', 'ignore')
			review_rating = r['rating']

			positive_score_review = 0
			negative_score_review = 0

			for search in nltk.word_tokenize(search_query.lower()):

				if p.singular_noun(search):
					search = p.singular_noun(search)
				try:
					review_adjectives = strip_proppers_POS(review_text, search)	
				except:
					continue
	
				for i in review_adjectives:
					positive_score_review += i[1]
					negative_score_review += i[2]

			positive_score_place += positive_score_review
			negative_score_place += negative_score_review
		
		res.append({'place_url':place['url'],'positive_score':  positive_score_place/len(reviews), 'negative_score': negative_score_place/len(reviews)})
		
	return res
		

if __name__ == '__main__':
	
	search_query = "swimming pool"
	location = "chicago"
	desired_sentiment = 1

	result_places = accumulate(search_query, location)
	
	if desired_sentiment == 1:
		sorted_places = sorted(result_places, key = lambda x:x['positive_score'], reverse = True)
	else:
		sorted_places = sorted(result_places, key = lambda x:x['negative_score'], reverse = True)

	print sorted_places[0]['place_url']
