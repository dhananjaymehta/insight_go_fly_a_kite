import json, yaml
from pyspark import SparkContext, SparkConf
from boto.s3.connection import S3Connection
from elasticsearch import Elasticsearch
from elasticsearch import helpers


with open("settings-template.yaml", 'r') as stream:
	try:
		SETTINGS = yaml.load(stream)
	except yaml.YAMLError as exc:
		print(exc)


wban = None
date = None
time = None
wind = None
stations = None


def getHeader(header):
	"""Gets the header for each .txt doc and finds the indicies for the
		columns wanted, accounting for changes in format"""
	global wban
	global date
	global time
	global wind

	if len(header.split(", ")) > 5:
		header = header.split(", ")
	elif len(header.split(",")) > 5:
		header = header.split(",")
	else:
		raise ValueError("Current splitting not working: " + header)
	if 'WBAN' in header:
		wban = header.index('WBAN')
	elif 'Wban Number' in header:
		wban = header.index('Wban Number')
	elif 'wban' in header:
		wban.index('wban')
	else:
		raise ValueError('WBAN not recognized')
	if 'Date' in header:
		date = header.index('Date')
	elif 'YearMonthDay' in header:
		date = header.index("YearMonthDay")
	else:
		raise ValueError('date not recognized')
	time = header.index('Time')
	if 'WindSpeed' in header:
		wind = header.index('WindSpeed')
	elif 'Wind Speed (kt)' in header:
		wind = header.index('Wind Speed (kt)')
	else:
		raise ValueError('windspeed not recognized')
	return wban, date, time, wind


def getUseful(data):
	wban_i = data[wban]
	date_i = data[date]
	time_i = data[time]
	wind_i = data[wind]
	try:
		wind_i = int(wind_i)
	except:
		wind_i = 0
	if wban_i in stations.keys():
		return ((stations[wban_i][0], stations[wban_i][1], date_i),\
									([time_i], [wind_i]))
	else:
		return ((0.000, 0.000, date_i), ([time_i], [wind_i]))


def formatL(line):
	lat = line[0][0]
	lon = line[0][1]
	date = line[0][2]
	times = line[1][0]
	winds = line[1][1]
	doc = {"_index": "batch_data",
			"_type": "data",
			"_source":
				{"location":
					{"lon":lon,
					"lat": lat},
				 "year": date[0:4],
				 "month": date[4:6],
				 "day": date[6:8],
				 "maxWs": max(winds),
				 "times": times,
				 "winds": winds
				 }
			}
	return doc


def sendOff(partition):
	es = Elasticsearch([SETTINGS['ES_IP']], http_auth=(SETTINGS['ES_USER_NAME'],\
								SETTINGS['ES_PASSWORD']), verify_certs=False)
	helpers.bulk(es, partition)


def main():
	conn = S3Connection(SETTINGS['AWS_KEY'],SETTINGS['AWS_SECRET_KEY'])
	print "ONE"
	bucket = conn.get_bucket(SETTINGS['S3_BUCKET'])
	print "TWO"
	sc = SparkContext(SETTINGS['SPARK_BC'])
	print "THREE"
	global stations
	with open('pysrc/all_stations.json') as data_file:
		stations = json.load(data_file)
	print "FOUR"
	path = SETTINGS['S3_PATH']
	print "PATH: ", path
	for fyle in bucket:
		print "FILE: ", fyle.name
		rdd = sc.textFile(path + fyle.name)
		# rdd = sc.textFile(path + "199607hourly.txt")
		header = rdd.first()
		getHeader(header)
		rdd = rdd.filter(lambda line: line != header)\
				.map(lambda line: line.split(','))
		rdd = rdd.filter(lambda line: len(line) >= wind)
		l1 = rdd.map(getUseful).reduceByKey(lambda a, b: (a[0] +\
												b[0], a[1] + b[1]))
		l2 = l1.map(formatL)
		l2.foreachPartition(sendOff)

if __name__ == '__main__':
	main()
