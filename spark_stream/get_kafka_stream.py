from __future__ import print_function
import redis, math, datetime, yaml
from pyspark import SparkContext, SparkConf
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
from elasticsearch import Elasticsearch
from elasticsearch import helpers

"""Processes the streaming data"""


with open("settings-template.yaml", 'r') as stream:
	try:
		SETTINGS = yaml.load(stream)
	except yaml.YAMLError as exc:
		print(exc)


def getAvg(line):
	"""Computes the average value by key in a given window and
		formats it in the correct way to send to the ES cluster"""
	lat, lon = line[0]
	sum_w, n = line[1]
	avg = sum_w / n
	date_time = str(datetime.datetime.now()).replace(':', '')\
											.replace('-', '')
	date = date_time[0:8]
	time = date_time[9:15]
	return {"_index": "stream_data",
			"_type": "data",
			"_source":
				{"location": {"lat": float(lat), "lon": float(lon)},
				 "day": date[6:8],
				 "year": date[0:4],
				 "month": date[4:6],
				 "time": time,
				 "wind": avg,
				 "hour":time[0:2],
				 "min": time[2:4]
				 }
			}


def getFormat(item):
	"""maps to the necessary format for the window being sent
		to ES"""
	lon, lat, wind, _, _ = item[1].split(',')
	try:
		wind = int(wind)
	except:
		wind = None
	return ((lat, lon), (wind, 1))


def send2Es(item):
	"""Sends the specified documents to the ES stream index for
		the day"""
	es = Elasticsearch([SETTINGS['ES_IP']], http_auth=(SETTINGS['ES_USER_NAME'],\
						 			SETTINGS['ES_PASSWORD']), verify_certs=False)
	helpers.bulk(es, item)


def getLLW(line):
	"""Formats the messages coming in for easy processing.
		to be sent to redis"""
	lon, lat, wind, _, _ = line[1].split(',')
	try:
		wind = int(wind)
	except:
		wind = None
	return (str(str(lon)+","+str(lat)), (wind, wind ** 2, 1))


def getStoke(st_dev, wind):
	"""Applies my desired stoke function to the data, stoke is a
		parabolic funciton with a value between 0 and 100, the higher
		the st_dev the lower the value"""
	stoke = (-0.1111 * (wind ** 2) + (6.67 * wind))
	if stoke > 0:
		return round(stoke / (1 + st_dev))
	else:
		return 0


def send2redis(rddP):
	"""Writes messages to redis through pipeline"""
	redis_server = SETTINGS['REDIS_IP']
	redis_session = redis.Redis(host=redis_server, port=6379, db=0)
	with redis_session.pipeline() as pipe:
		for data in rddP:
			pipe.set(data[0], data[1])
		pipe.execute()


def getSTD(item):
	"""Computes the standard deviation by key in a window of time,
		using sketching"""
	num2 = item[1][1]
	num = item[1][0]
	n = item[1][2]
	std = math.sqrt((num2/n) - ((num ** 2) / n))
	avg = num / n
	return (item[0], (avg, getStoke(std, avg)))


def main():
	"""Runs and specifies map reduce jobs for streaming data. Data
		is processed in 2 ways to be sent both to redis and ES"""
	sc = SparkContext(SETTINGS['SPARK_C'])
	ssc = StreamingContext(sc, 30)

	my_topic = 'wind_stream'
	brokers = SETTINGS["KAFKA_BROKER1"] + "," + SETTINGS["KAFKA_BROKER2"]\
			 + "," + SETTINGS["KAFKA_BROKER3"] + "," + SETTINGS["KAFKA_BROKER4"]

	directKafkaStream2 = KafkaUtils.createDirectStream(ssc, \
							[my_topic], {"metadata.broker.list": brokers})

	window_s = directKafkaStream2.window(300, 150).map(getLLW)\
				.reduceByKey(lambda a, b: (a[0] + b[0], a[1] + \
												b[1], a[2] + b[2]))\
				.map(getSTD)
	winmr2 = window_s.foreachRDD(lambda rdd: rdd\
										.foreachPartition(send2redis))

	stream = directKafkaStream2.window(3600, 3600).map(getFormat)\
				.reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1]))\
				.map(getAvg)
	stream.foreachRDD(lambda rdd: rdd.foreachPartition(send2Es))

	ssc.start()
	ssc.awaitTermination()

if __name__ == '__main__':
	main()
