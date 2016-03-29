#This contains in-house code. Replaced by Wit API.

import nltk

def processLanguage(query):
	try:
		tokenized = nltk.word_tokenize(query)
		tagged = nltk.pos_tag(tokenized)
		namedEnt = nltk.ne_chunk(tagged,binary=True)
		return namedEnt
	except Exception, e:
		 print str(e)

def get_entities(query):
	tokenized = nltk.word_tokenize(query)
	if "hotel" in tokenized or "hotels" in tokenized:
		return "hotels"
	elif "flight" in tokenized or "flights" in tokenized:
		return "flights"
	elif "rental" in tokenized or "rentals" in tokenized:
		return "holiday rentals"
	elif "restaurant" in tokenized or "restaurants" in tokenized:
		return "restaurants"
	elif "destination" in tokenized or "destinations" in tokenized:
		return "destinations"
	else:
		"No entity found"

query = "find the best Italian restaurant near Seattle Washington"

tree_entities = processLanguage(query)
defined_entities = get_entities(query)

print tree_entities
print defined_entities

myNE = [] 
myNouns = []

for i in tree_entities:
	if "NE" in str(i):  
		 myNE.append(' '.join(j[0] for j in i.leaves() if 'NN' in j[1]))
	elif "NN" in str(i):
		if defined_entities:
			if i[0].lower() not in defined_entities:  
				myNouns.append(i[0].lower())
		else:
			myNouns.append(i[0].lower())
	
print myNE
print myNouns

