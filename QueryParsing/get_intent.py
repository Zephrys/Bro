import wit
import json
import config

def call_wit(query):

	wit.init()
	res = {}	
	response = json.loads(wit.text_query(query, config.access_token))
	
	outcome = response['outcomes'][0]
	
	intent = outcome['intent']
	res['intent'] = intent

	entities = outcome['entities']	

	if 'location' in entities:
		location = entities['location'][-1]
		if location['suggested']:
			res['location'] = location['value']
	
	if 'search_query' in entities:
		search = entities['search_query'][-1]
		if search['suggested']:
			res['search'] = search['value']
  
	
	return res

print call_wit("Hotels with the best view of the Grand Canyon in USA")
