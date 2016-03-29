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
	url = "https://www.tripadvisor.in/Search?q=%s&geo=%s&actionType=updatePage&ssrc=%s&o=0&ajax=search&ajax=search" %(keyword, tripadvisor_code, entityMap[entityType])
	response = requests.get(url)
	soup = BeautifulSoup(response.text)



	data = {'askForConfirmation': 'false', 'cc': '', 'mode': 'filterReviews', 'q': keyword,  'returnTo': url, 't': ''}



def main(keyword, place, entityType = 'HOTEL'):
	if reviews_db.count({'keyword': keyword.lower(), 'place': place.lower()}) > 0:
		return reviews_db.find({'keyword': keyword, 'place': place})
	else:
		getReviews(keyword, place)
		return reviews_db.find({'keyword': keyword.lower(), 'place': place.lower()})