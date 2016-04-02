from keys import *
from twython import Twython
from twython import TwythonStreamer
import sys
import os
sys.path.insert(0, os.path.abspath("."))
from QueryParsing import get_intent
from KnowledgeBases.TripAdvisor import TripAdvisor
from SemanticRanks import ranks

t = Twython(app_key=consumer_key, app_secret=consumer_secret,
            oauth_token=access_token, oauth_token_secret=access_token_secret)


class HashStreamer(TwythonStreamer):
    def on_success(self, data):
        if 'text' in data:
            print data['text'].encode('utf-8')
            tokens = data['text'].split()
            print ' '.join([x for x in tokens if '#' not in x])
            response = get_intent.call_wit(' '.join([x for x in tokens
                                                     if '#' not in x]))
            boolean = False
            if response['intent'] == 'get_hotels':
                boolean = TripAdvisor.main(response['search'],
                                           response['location'], 'HOTEL')
            elif response['intent'] == 'get_restaurants':
                boolean = TripAdvisor.main(response['search'],
                                           response['location'], 'RESTAURANT')
            if boolean:
                output = ranks.integrated(response['search'],
                                          response['location'])

            status = "Find the Best " + response['search'] + "in "
            status += response['location'] + "here:"

            status = "@" + data['user']['screen_name'] + status + output
            t.update_status(status=status)

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
