from keys import *
from twython import Twython
from twython import TwythonStreamer
from QueryParsing import get_intent
import re
from KnowledgeBases.TripAdvisor import TripAdvisor
from SemanticRanks import ranks

t = Twython(app_key=consumer_key, app_secret=consumer_secret,
            oauth_token=access_token, oauth_token_secret=access_token_secret)


class HashStreamer(TwythonStreamer):
    def on_success(self, data):
        print data
        if 'text' in data  and 1==2:
            print data['text'].encode('utf-8')
            response = get_intent.call_wit(' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)"," ",data['text']).split()))
            boolean = False
            if response[0] == 'get_hotels':
            	boolean = TripAdvisor.main(response[1], response[2], 'HOTEL')
            elif response[0] == 'get_restaurants':
            	boolean = TripAdvisor.main(response[1], response[2], 'RESTAURANT')
            if boolean:
                output = ranks.integrated(response[1], response[2])
                t.update_status(output)

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


# if __name__ == '__main__':
#     activate_stream()
