from keys import *
from twython import Twython
from twython import TwythonStreamer
import sys
import os
sys.path.insert(0, os.path.abspath("."))
from QueryParsing import get_intent
from KnowledgeBases.TripAdvisor import TripAdvisor
from SemanticRanks import ranks
import datetime
from pymongo import MongoClient
import requests
from io import BytesIO

client = MongoClient('mongodb://localhost:27017/')
db = client.Bro
unmatched_db = db.unmatched


t = Twython(app_key=consumer_key, app_secret=consumer_secret,
            oauth_token=access_token, oauth_token_secret=access_token_secret)


class HashStreamer(TwythonStreamer):
    def on_success(self, data):
        if 'text' in data:
            tokens = data['text'].split()
            print ' '.join([x for x in tokens if '#' not in x])
            response = get_intent.call_wit(' '.join([x for x in tokens
                                                     if '#' not in x]))
            boolean = False
            print response

            if not response.has_key('location') or not response.has_key('search'):
                return

            if response['intent'] == 'get_hotels':
                boolean = TripAdvisor.main(response['search'],
                                           response['location'], 'HOTEL')
            elif response['intent'] == 'get_restaurants':
                boolean = TripAdvisor.main(response['search'],
                                           response['location'], 'RESTAURANT')
            if boolean:
                output, image = ranks.integrated(response['search'],
                                          response['location'])
                status = "Find the Best " + response['search'] + " in "
                status += response['location'] + " here! "

                found_match = False
                if '#match' in data['text'] and response['intent'] == 'get_restaurants' and boolean:
                    unmatched = unmatched_db.find({'keyword': response['search'], 'place': response['location']})
                    for match in unmatched:
                        if (datetime.datetime.now() - match['timestamp']).seconds/60.0 < 30 and match['nick'] != data['user']['screen_name']:
                            found_match = match['nick']
                            break
                        unmatched_db.remove({'keyword': response['search'],
                            'place': response['location'], 'nick': match['nick'],
                            'timestamp': match['timestamp']})

                status = "@" + data['user']['screen_name'] + " " +  status + output

                if found_match:
                    status+= " meet %s, they are also looking to grab a bite." %(found_match)
                elif '#match' in data['text']:
                    unmatched_db.insert({'keyword': response['search'], 'place': response['location'],
                        'nick': data['user']['screen_name'], 'timestamp': datetime.datetime.now()})
                    status += ' couldnt find a match. hold on!'

            else:
                status = "@ " + data['user']['screen_name']

            print '[%s]: %s' %(datetime.datetime.now(), status)
            img = requests.get(image).content

            t.post('statuses/update_with_media', params={'status': status},
                files= {'media': (image, BytesIO(img))})

    def on_error(self, status_code, data):
        print status_code


def get_topic_tweets(topic, count):
    tweets = t.search(q=topic, count=count, language="en")
    collections = tweets['statuses']
    res = {}
    res['topic'] = topic
    res['tweets'] = [i['text'] for i in collections]
    return res


def activate_stream():
    stream = HashStreamer(consumer_key, consumer_secret,
                          access_token, access_token_secret)

    stream.statuses.filter(track='#AskBro')

if __name__ == '__main__':
    activate_stream()
