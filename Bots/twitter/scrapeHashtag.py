from twython import Twython

t = Twython(app_key='yOc6qbMtrTRJ5QmHpy640yCS9', app_secret='4mPSvT4y7T3auJA3Z5iytIIRdvKMnOqJug4fHTqeakf5wh4bo0', oauth_token='2892300355-9xhU0WMC91WRUjT80r8mzmrBIUOI9gMfcN7tvuB', oauth_token_secret='TNZ06Pt8hS2OYCVfDDJ1YnP4qQQYkFzL9FaxSptZWFJgk')
   

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
