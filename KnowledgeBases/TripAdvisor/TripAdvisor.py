from bs4 import BeautifulSoup
import requests
from pymongo import MongoClient
from tornado import ioloop, httpclient
import functools
from urllib import quote, urlencode
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client.Bro
reviews_db = db.tripadvisor_reviews
place_db = db.tripadvisor_places

def moreReviewHandler(persistent, name, response):
	persistent['i'] -= 1
	if response.code != 200:
		return

	if persistent['i'] == 0:
		ioloop.IOLoop.instance().stop()

	soup = BeautifulSoup(response.body)

	ratings = [x['alt'] for x in soup('img', {'class': 'sprite-rating_s_fill'})]
	ratingDates = [x.text for x in soup('span', {'class': 'ratingDate'})]
	partials = [x.text for x in soup('p', {'class': 'partial_entry'}) if x.parent['class'][0] == 'entry']

	for x in xrange(0, len(partials)):
		data = {'review': partials[x], 'rating': ratings[x], 'ratingDates': ratingDates[x]}
		persistent['results'][name]['reviews'].append(data)


def hotelHandler(persistent, response):
	persistent['i'] -= 1
	if response.code != 200:
		return
	if persistent['i'] == 0:
		ioloop.IOLoop.instance().stop()

	soup = BeautifulSoup(response.body)
	urls = [x['href'][:-8] for x in soup('a', {'class': 'review-count'})]
	ratings = [x['alt'] for x in soup('img', {'class': 'sprite-ratings'})]

	persistent['urls'] = persistent['urls'] + urls
	persistent['url_ratings'] = persistent['url_ratings'] + urls

def reviewHandler(persistent, hotel_url, keyword, rating, response):
	persistent['i'] -= 1
	if response.code != 200:
		return

	if persistent['i'] == 0:
		ioloop.IOLoop.instance().stop()

	soup = BeautifulSoup(response.body)

	name = soup('div', {'class': 'warTitle'})[-1].span.text[21:]

	ratings = [x['alt'] for x in soup('img', {'class': 'sprite-rating_s_fill'})]
	ratingDates = [x.text for x in soup('span', {'class': 'ratingDate'})]
	partials = [x.text for x in soup('p', {'class': 'partial_entry'}) if x.parent['class'][0] == 'entry']
	urls = [x['href'] for x in soup('a', {'class': 'pageNum taLnk'})]

	for url in urls:
		url = 'https://www.tripadvisor.com' + url
		data = {'askForConfirmation': 'false', 'mode': 'filterReviews', 'q': keyword, 'returnTo': url}
		persistent['moreReviews'].append({'url': url, 'data': data, 'name': name})

	persistent['results'][name] = {}
	persistent['results'][name]['rating'] = rating

	persistent['results'][name]['reviews'] = []
	persistent['results'][name]['url'] = hotel_url

	for x in xrange(0, len(partials)):
		data = {'review': partials[x], 'rating': ratings[x], 'ratingDates': ratingDates[x]}
		persistent['results'][name]['reviews'].append(data)


def getReviews(keyword, place, entityType):
	if place_db.count({'place': place}) == 0:
		url = 'https://www.tripadvisor.in/TypeAheadJson?query=%s&action=API&uiOrigin=GEOSCOPE&source=GEOSCOPE&interleaved=true&types=geo,theme_park&neighborhood_geos=true&link_type=geo,hotel,vr,attr,eat,flights_to,nbrhd,tg&details=true&max=12&injectNeighborhoods=true'%(quote(place, safe=''))
		try:
			response = requests.get(url)
			if response.status_code == 200:
				data = response.json()
				data = data['results'][0]
				place_db.insert({'advisor': data, 'place': place})
			else:
				print url
				print response.status_code
				return False
		except:
			import traceback; traceback.print_exc();

	data = place_db.find_one({'place': place})['advisor']
	tripadvisor_code = data['value']
	print tripadvisor_code

	entityMap = {'HOTEL': 'h', 'RESTAURANT': 'e', 'ALL': 'a', 'ATTRACTIONS': 'A'}

	url = "https://www.tripadvisor.in/Search?q=%s&geo=%s&actionType=updatePage&ssrc=%s&o=0&ajax=search" %(keyword, tripadvisor_code, entityMap[entityType])
	response = requests.get(url)
	soup = BeautifulSoup(response.text)

	#check if there are some results specific to the city
	#Idea in the world queries scope 1.
	#Trying to support in the world queries
	scope = int(soup('input', {'id': 'scope'})[0]['value'])
	if scope == 1 and 'place' not in ['globe', 'world']:
		reviews_db.insert({'keyword': keyword, 'place': place, 'results': {}, 'entity': entityType}, check_keys=False)
		return

	maxOffset = 0
	if len(soup('a', {'class': 'pageNumber'})) > 0:
		maxOffset = (int(soup('a', {'class': 'pageNumber'})[-1].text) - 1 ) * 30
	print 'Number of results %d' %(maxOffset)

	urls = [x['href'][:-8] for x in soup('a', {'class': 'review-count'})]
	ratings = [x['alt'] for x in soup('img', {'class': 'sprite-ratings'})]

	http_client = httpclient.AsyncHTTPClient()
	persistent = {}
	persistent['i'] = 0
	persistent['urls'] = urls
	persistent['url_ratings'] = ratings

	for offset in xrange(30, maxOffset+1, 30):
		persistent['i'] += 1
		binding = functools.partial(hotelHandler, persistent)
		url = "https://www.tripadvisor.in/Search?q=%s&geo=%s&actionType=updatePage&ssrc=%s&o=%d&ajax=search" %(quote(keyword, safe=''), tripadvisor_code, entityMap[entityType], offset)
		http_client.fetch(url, binding)
	if persistent['i'] !=0:
		ioloop.IOLoop.instance().start()

	print 'Hotels Fetched'

	http_client = httpclient.AsyncHTTPClient()

	persistent['i'] = 0
	persistent['results'] = {}
	persistent['moreReviews'] = []

	print 'digging into reviews'
	for url in persistent['urls']:
		rating = persistent['url_ratings'][persistent['urls'].index(url)]
		url = 'https://www.tripadvisor.com' + url
		persistent['i'] += 1
		binding = functools.partial(reviewHandler, persistent, url, keyword, rating)
		data = {'askForConfirmation': 'false', 'mode': 'filterReviews', 'q': keyword, 'returnTo': url}
		http_client.fetch(url, binding, method= "POST", body = urlencode(data))

	if persistent['i'] != 0:
		ioloop.IOLoop.instance().start()

	print 'digging into even more reviews'
	http_client = httpclient.AsyncHTTPClient()
	persistent['i'] = 0
	for urls in persistent['moreReviews']:
		persistent['i'] +=1
		binding = functools.partial(moreReviewHandler, persistent, urls['name'])
		http_client.fetch(urls['url'], binding, method = "POST", body = urlencode(urls['data']))

	if persistent['i'] != 0:
		ioloop.IOLoop.instance().start()

	reviews_db.insert({'keyword': keyword, 'place': place, 'results': persistent['results'], 'entity': entityType}, check_keys=False)
	return True

def main(keyword, place, entityType = 'HOTEL'):
	keyword = keyword.lower()
	place = place.lower()

	if place_db.count({'place': 'world'}) == 0:
		place_db.insert({'place': 'world', 'advisor' : {'value': 1} })

	if reviews_db.count({'keyword': keyword, 'place': place, 'entity': entityType}) > 0:
		return True
	else:
		return getReviews(keyword, place, entityType)