from twython import Twython
from keys import *

t = Twython(app_key=consumer_key, app_secret=consumer_secret, oauth_token=access_token, oauth_token_secret=access_token_secret)


def get_topic_tweets(topic, count):
	tweets = t.search(q=topic, count = count,language="en")
	collections = tweets['statuses']
	res = {}
	res['topic'] = topic
	res['tweets'] = [i['text'] for i in collections]
	return res

if __name__ == '__main__':
	hashtag = '#mondaymotivation'
	count = 10
	print get_topic_tweets(hashtag,count)
