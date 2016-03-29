from bs4 import BeautifulSoup
import requests
from pymongo import MongoClient
from tornado import ioloop, httpclient
import functools
from urllib import quote, urlencode

client = MongoClient('mongodb://localhost:27017/')
db = client.Bro
reviews_db = db.tripadvisor
place_db = db.tripadvisor



def hotelHandler(persistent, response):
	print 'hotel handler %d' %(response.code)
	print response.effective_url
	persistent['i'] -= 1
	if response.code != 200:
		return
	if persistent['i'] == 0:
		ioloop.IOLoop.instance().stop()

	soup = BeautifulSoup(response.body)
	urls = [x['href'][:-8] for x in soup('a', {'class': 'review-count'})]
	for x in urls:
		print x

	persistent['urls'] = persistent['urls'] + urls

def reviewHandler(persistent, hotel_url, keyword, response):
	print 'Review handler %d' %response.code
	print response.effective_url
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

	http_client_2 = httpclient.AsyncHTTPClient()
	try:
		for url in urls:
			url = 'https://www.tripadvisor.com' + url
			data = {'askForConfirmation': 'false', 'mode': 'filterReviews', 'q': keyword, 'returnTo': url}
			response = requests.post(url, data=data)
			soup = BeautifulSoup(response.text)
			ratings = ratings +  [x['alt'] for x in soup('img', {'class': 'sprite-rating_s_fill'})]
			ratingDates = ratingDates + [x.text for x in soup('span', {'class': 'ratingDate'})]
			partials = partials + [x.text for x in soup('p', {'class': 'partial_entry'}) if x.parent['class'][0] == 'entry']

	except:
		pass

	persistent['results'][hotel_url] = {}
	persistent['results'][hotel_url]['reviews'] = []

	for x in xrange(0, len(partials)):
		data = {'review': partials[x], 'rating': ratings[x], 'ratingDates': ratingDates[x]}
		persistent['results'][hotel_url]['reviews'].append(data)

	persistent['results'][hotel_url]['name'] = name

def getReviews(keyword, place, entityType):
	if place_db.count({'place': place}) == 0:
		url = 'https://www.tripadvisor.in/TypeAheadJson?query=%s&action=API&uiOrigin=GEOSCOPE&source=GEOSCOPE&interleaved=true&types=geo,theme_park&neighborhood_geos=true&link_type=geo,hotel,vr,attr,eat,flights_to,nbrhd,tg&details=true&max=1&injectNeighborhoods=true'%(quote(place, safe=''))
		try:
			response = requests.get(url)
			if response.status_code == 200:
				data = response.json()
				data = data['results'][0]
				place_db.insert({'advisor': data, 'place': place})
			else:
				return 'Fail'
		except:
			import traceback; traceback.print_exc();

	data = place_db.find_one({'place': place})['advisor']
	tripadvisor_code = data['value']
	print tripadvisor_code

	entityMap = {'HOTEL': 'h', 'RESTAURANT': 'e', 'ALL': 'a', 'ATTRACTIONS': 'A', 'HOLIDAY_HOME': ''}

	url = "https://www.tripadvisor.in/Search?q=%s&geo=%s&actionType=updatePage&ssrc=%s&o=0&ajax=search" %(keyword, tripadvisor_code, entityMap[entityType])
	response = requests.get(url)
	soup = BeautifulSoup(response.text)
	maxOffset = 0
	if len(soup('a', {'class': 'pageNumber'})) > 0:
		maxOffset = (int(soup('a', {'class': 'pageNumber'})[-1].text) - 1 ) * 30
	print 'Number of results %d' %(maxOffset)

	urls = [x['href'][:-8] for x in soup('a', {'class': 'review-count'})]
	#fetch all these pages assynchronously
	http_client = httpclient.AsyncHTTPClient()
	persistent = {}
	persistent['i'] = 0
	persistent['urls'] = urls

	for offset in xrange(30, maxOffset+1, 30):
		persistent['i'] += 1
		binding = functools.partial(hotelHandler, persistent)
		url = "https://www.tripadvisor.in/Search?q=%s&geo=%s&actionType=updatePage&ssrc=%s&o=%d&ajax=search" %(quote(keyword, safe=''), tripadvisor_code, entityMap[entityType], offset)
		print url
		http_client.fetch(url, binding)

	ioloop.IOLoop.instance().start()
	print 'Hotels Fetched'

	http_client = httpclient.AsyncHTTPClient()
	persistent['i'] = 0
	persistent['results'] = {}

	print 'digging into reviews'
	for url in persistent['urls']:
		url = 'https://www.tripadvisor.com' + url
		persistent['i'] += 1
		binding = functools.partial(reviewHandler, persistent, url, keyword)
		data = {'askForConfirmation': 'false', 'mode': 'filterReviews', 'q': keyword, 'returnTo': url}
		http_client.fetch(url, binding, method= "POST", body = urlencode(data))

	ioloop.IOLoop.instance().start()

	from pprint import pprint
	pprint(persistent)
	db.insert_one({'keyword': keyword, 'place': place, 'results': persistent['results']})


def main(keyword, place, entityType = 'HOTEL'):
	keyword = keyword.lower()
	place = place.lower()

	if reviews_db.count({'keyword': keyword, 'place': place}) > 0:
		return reviews_db.find_one({'keyword': keyword, 'place': place})
	else:
		getReviews(keyword, place, entityType)
		return reviews_db.find({'keyword': keyword.lower(), 'place': place.lower()})

main('swimming pool', 'chicago')