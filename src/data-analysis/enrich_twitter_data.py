#!/usr/bin/env python
import json
import boto3

#Use a profile for now...
boto3.setup_default_session(profile_name='rob')

#Size of each 'chunk' required.
#Currently comprehend supports
chunk_size = 25

#Details for day to analyse
year='2018'
month='04'
day='17'

s3_resource = boto3.resource('s3')
comprehend_client = boto3.client('comprehend')

bucket = s3_resource.Bucket('sentiment-analysis-pipeline-datapipeline-s3bucket-h8gq3b8ccovj')
objs = bucket.objects.filter(Prefix='firehose/{}/{}/{}/'.format(year,month,day))
tweet_list=[]
for obj in objs:
  tweet_list.extend(obj.get()['Body'].read().decode('utf-8').split('\n'))

#Remove empty strings
tweet_list = [x for x in tweet_list if x]
 
#List comprehension.  Chunk our list into n sized lists.  Each of these will be a request to 
chunked_tweet_list = [tweet_list[i * chunk_size:(i + 1) * chunk_size] for i in range((len(tweet_list) + chunk_size - 1) // chunk_size )] 

results_list=[]

for chunk_index, chunk_list in enumerate(chunked_tweet_list):
    response_sentiment = comprehend_client.batch_detect_sentiment(
        TextList=chunk_list,
        LanguageCode='en'
    )

    response_entities = comprehend_client.batch_detect_entities(
        TextList=chunk_list,
        LanguageCode='en'
    )

    reindex_results_list = []
    for result_sentiment,result_entity in zip(response_sentiment['ResultList'],response_entities['ResultList']):

      merged_result = dict()
      merged_result.update(result_sentiment)
      merged_result.update(result_entity)
      merged_result_tweet_index = merged_result['Index']
      merged_result_new_index = merged_result_tweet_index + chunk_index*chunk_size
      merged_result['Index'] = merged_result_new_index
      merged_result['tweet_text'] = tweet_list[merged_result_new_index]
      reindex_results_list.append(merged_result)
    results_list.extend(reindex_results_list)
    if chunk_index >= 10:
      break

print(json.dumps(results_list))

#print(response)