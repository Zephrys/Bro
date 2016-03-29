from bs4 import BeautifulSoup
import requests
from pymongo import MongoClient
import re
from datetime import datetime
from util import get_price_range,make_soup
from tornado import ioloop, httpclient
import functools

client = MongoClient('mongodb://localhost:27017/')
db = client.Bro
reviews_db = db.tripadvisor
place_db = db.tripadvisor



def hotelHandler(persistent, response):
	persistent['i'] -= 1
	if response.code != 200:
		return
	if persistent['i'] == 0:
		ioloop.IOLoop.instance().stop()

	soup = BeautifulSoup(response.body)
	urls = [x['href'][-8] for x in soup({'a', {'class': 'review-count'})]

	persistent['urls'] = count['urls'] + urls

def reviewHandler(persistent, hotel_url, response):
	persistent['i'] -= 1
	if response.code != 200:
		return

	if persistent['i'] == 0:
		ioloop.IOLoop.instance().stop()

	soup = BeautifulSoup(response.body)

	name = soup('div', {'class': 'warTitle'}).span.text[21:]

	ratings = [x['alt'] for x in soup('img', {'class': 'sprite-rating_s_fill'})]
	ratingDates = [x.text for x in soup('span', {'class': 'ratingDate'})]
	partials = [x.text[:x.find('<span class="partnerRvw">')] for x in soup('p', {'class': 'partial_entry'})]
	urls = [x['href'] for x in soup('a', {'class': 'pageNum taLnk'})]

	for url in urls:
		response = requests.get(url)
		soup = BeautifulSoup(response.text)
		ratings = ratings +  [x['alt'] for x in soup('img', {'class': 'sprite-rating_s_fill'})]
		ratingDates = ratingDates + [x.text for x in soup('span', {'class': 'ratingDate'})]
		partials = partials + [x.text[:x.find('<span class="partnerRvw">')] for x in soup('p', {'class': 'partial_entry'})]

	persistent['results'][hotel_url] = {}
	for x in xrange(0, len(partials)):
		data = {'review': partials[x], 'rating': ratings[x], 'ratingDates': ratingDates[x]}
		persistent['results'][hotel_url].append(data)

	persistent['results'][hotel_url]['name'] = name


def getReviews(keyword, place, entityType):
	if place_db.count({'place': place}) == 0:
		url = 'https://www.tripadvisor.in/TypeAheadJson?query=%s&action=API&uiOrigin=GEOSCOPE&source=GEOSCOPE&interleaved=true&types=geo%2Ctheme_park&neighborhood_geos=true&link_type=geo%2Chotel%2Cvr%2Cattr%2Ceat%2Cflights_to%2Cnbrhd%2Ctg&details=true&max=1&injectNeighborhoods=true'%(place)
		try:
			response = requests.get(url)
			if response.status_code == 200:
				data = response.json()
				data = data['results'][0]
				place_db.insert({'advisor' data, 'place': place})
			else:
				return 'Fail'
		except:
			import traceback; traceback.print_exc();

	data = place_db.find_one({'place': place})['advisor']
	tripadvisor_code = data['value']

	entityMap = {'HOTEL': 'h', 'RESTAURANT': 'e', 'ALL': 'a', 'ATTRACTIONS': 'A', 'HOLIDAY_HOME': ''}

	url = "https://www.tripadvisor.in/Search?q=%s&geo=%s&actionType=updatePage&ssrc=%s&o=0&ajax=search" %(keyword, tripadvisor_code, entityMap[entityType])
	response = requests.get(url)
	soup = BeautifulSoup(response.text)
	maxOffset = (int(soup('a', {'class': 'pageNumber'})[-1].text) - 1 ) * 30
	print 'Number of results %d' %(maxOffset)

	urls = [x['href'][-8] for x in soup({'a', {'class': 'review-count'})]

	#fetch all these pages assynchronously
	http_client = httpclient.AsyncHTTPClient()
	persistent = {}
	persistent['i'] = 0
	persistent['urls'] = urls
	for offset in xrange(30, maxOffset+1, 30):
		persistent['i'] += 1
		binding = functools.partial(hotelHandler, persistent)
		url = "https://www.tripadvisor.in/Search?q=%s&geo=%s&actionType=updatePage&ssrc=%s&o=%d&ajax=search" %(keyword, tripadvisor_code, entityMap[entityType], offset)
		http_client.fetch(url, binding)

	ioloop.IOLoop.instance().start()
	print 'Hotels Fetched'

	http_client = httpclient.AsyncHTTPClient()
	persistent['i'] = 0
	persistent['results'] = {}

	for url in persistent['urls']:
		persistent['i'] += 1
		binding = functools.partial(reviewHandler, persistent, url)
		data = {'askForConfirmation': 'false', 'cc': '', 'mode': 'filterReviews', 'q': keyword,  'returnTo': url, 't': ''}
		http_client.fetch(url, binding, method= "POST", body = data)

	ioloop.IOLoop.instance().start()

	db.insert_one({'keyword': keyword, 'place': place, 'results': persistent['results']})


def main(keyword, place, entityType = 'HOTEL'):
	if reviews_db.count({'keyword': keyword.lower(), 'place': place.lower()}) > 0:
		return reviews_db.find({'keyword': keyword, 'place': place})
	else:
		getReviews(keyword, place)
		return reviews_db.find({'keyword': keyword.lower(), 'place': place.lower()})