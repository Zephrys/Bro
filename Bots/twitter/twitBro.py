from tweepy import OAuthHandler
from keys import *


auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)


def isInteresting():
    pass
