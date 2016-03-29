from tweepy.streaming import StreamListener
from tweepy import Stream
from tweepy import OAuthHandler


consumer_key = '3SQKP8cW8WKoSfuqCurWsLFc'
consumer_secret = '4efO0d9F89M0ESdDMJltMS7nrXzDZekLedXDuSHv2yHmbdpiHr'
access_token = '3140828020-EVDYXgTJkq40ETojrPnYeXYi0SiACbHKVpYkY6K'
access_token_secret = 'ueFgkJOw5rksJwB1PSFTMmbbS3P8Y3CK3710blQLjNpZy'

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)


def isInteresting():
	pass

