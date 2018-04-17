#!/usr/bin/env python
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import json
import boto3

from http.client import IncompleteRead
from urllib3.exceptions import ReadTimeoutError

import configparser
config = configparser.ConfigParser()
config.read('config.ini')
twitter_creds=config['twitter_creds']

# set up stream listener
class listener(StreamListener):
    def __init__(self):
        #Only include tweets in English.
        #'AWS Comprehend' currently supports both English and Spanish.
        self.supported_languages=['en']
        #Ignore compliance messages that have no content, e.g. delete requests, statuses that have been witheld (copyright)
        #Ignore retweets of other tweets.  Not sure if this is a good idea or not, but gives you more organic data.
        self.ignored_tweet_characteristics=['delete','status_withheld','scrub_geo','user_withheld','user_update','retweeted_status']
        self.firehose_client = boto3.client('firehose', region_name="eu-west-1")

    def on_data(self, data):
        tweet=json.loads(data)
        #If there are any characteristics we want to ignore, skip.
        if not any(key in self.ignored_tweet_characteristics for key in tweet):
            if tweet['lang'] in self.supported_languages:
                #Handle the 140/280 truncated tweets.
                if 'truncated' in tweet:
                    if tweet['truncated'] is False:
                        self.write_tweet(tweet['text'].replace("\n",""))
                    else:
                        self.write_tweet(tweet['extended_tweet']['full_text'].replace("\n",""))
    def on_error(self, status):
        #¯\_(ツ)_/¯ - worry about this later
        print(status)
    def on_exception(self, exception):
        #¯\_(ツ)_/¯ - worry about this later
        print(exception)

    def write_tweet(self,tweet):
        try:
            response = self.firehose_client.put_record(
                DeliveryStreamName='sentiment-analysis-pipeline-DataPip-deliverystream-15W54XALZWF2Z',
                Record={
                    'Data': tweet+'\n'
                }
            )
        except Exception as e:
            print(e)
            print("Problem pushing to firehose")

boto3.setup_default_session(profile_name='rob')

def start_stream(auth):
    while True:
        try:
            twitterStream = Stream(auth, listener())
            twitterStream.sample()
        except (IncompleteRead, ReadTimeoutError) as e :
            print(e)
            continue

auth = OAuthHandler(twitter_creds['consumer_key'], twitter_creds['consumer_secret'])
auth.set_access_token(twitter_creds['access_token'], twitter_creds['access_token_secret'])
start_stream(auth)
