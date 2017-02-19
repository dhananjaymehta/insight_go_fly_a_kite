import json, yaml
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
from pyspark import SparkContext, SparkConf
from elasticsearch import Elasticsearch


"""Move the data streamed daily into the elasticsearch streaming
	index into the historical index at the end of the day and
	reformats it"""


with open("../conf/settings-template.yaml", 'r') as stream:
	try:
		settings = yaml.load(stream)
	except yaml.YAMLError as exc:
		print(exc)


def makePair(item):
	item = item['_source']
	date = item['date']
	location = item['location']
	wind = item['wind']
	time = item['time']
	return ((location[0], location[1], date), ([time], [wind]))


def sendOff(item):
	if len(item['date']) > 5:
		es = Elasticsearch([ES_IP], http_auth=(ES_USER_NAME,\
									ES_PASSWORD), verify_certs=False)
		for line in item:
			es.index(index='S3_historical_data', doc_type='inputs',\
								body=line)


def formatL(item):
	ll = item[0][0]
	day = item[0][1]
	times = item[1][0]
	winds = item[1][1]
	doc = {"location": ll, "date": day, "maxWS": max(winds),\
							"times": times, "winds": winds}
	return doc


sc = SparkContext()
es = Elasticsearch([SETTINGS[ES_IP]], http_auth=(settings[ES_IP],\
						SETTINGS[ES_PASSWORD]),	verify_certs=False)
test = es.search(index='stream_data')
num_docs = test['hits']['total']
res = es.search(index="stream_test", size=num_docs)
sc.parallelize(res['hits']['hits']).map(makePair)\
			.reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1]))\
			.map(formatL).foreachPartition(sendOff)
