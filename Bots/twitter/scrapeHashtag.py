from keys import *
from twython import Twython
from twython import TwythonStreamer

t = Twython(app_key=consumer_key, app_secret=consumer_secret,
            oauth_token=access_token, oauth_token_secret=access_token_secret)


class HashStreamer(TwythonStreamer):
    def on_success(self, data):
        if 'text' in data:
                    print data['text'].encode('utf-8')

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

    stream.statuses.filter(track='#DonaldTrump, #bro')

if __name__ == '__main__':
    # hashtag = '#mondaymotivation'
    # count = 10
    # print get_topic_tweets(hashtag, count)
    activate_stream()
