import os, sys, json, urllib2, random, datetime, yaml
import pylab as pl
from kafka import KafkaConsumer, KafkaProducer
import add_2_geo


# with open("../conf/settings-template.yaml", 'r') as stream:
# 	try:
# 		settings = yaml.load(stream)
# 	except yaml.YAMLError as exc:
# 		print(exc)


mytopic = "wind_stream"
producer = KafkaProducer(bootstrap_servers=['localhost:9092'])


def get_stations(stations):
	"""Call the noaa api for the lat lon of each station"""
	i = 0
	for key in stations:
		print "number: ", i
		current = call_wind_api(stations[key][0], stations[key][1])
		i += 1


def simulate(lat, lon, wind, date, time):
	"""Simulate windspeed and station locations for the area
		surrounding a NOAA station, wind is within a degree of measured
		windspeed"""
	max_lat = lat + 0.5000
	min_lat = lat - 0.5000
	max_lon = lon + 0.5000
	min_lon = lon - 0.5000
	# change when higher resolution wanted
	lat_interval = 0.04
	lon_interval = 0.04
	lat_range = pl.frange(min_lat, max_lat, lat_interval)
	lon_range = pl.frange(min_lon, max_lon, lon_interval)
	add_2_geo.add_locs(lat, lon, lat_range, lon_range)
	for i in lat_range:
		for j in lon_range:
			gust = random.uniform(-0.3, 0.3)
			wind_i = wind + (wind * gust)
			if i is not lat and j is not lon:
				data = (str(str(j) + ',' + str(i) + ',' +\
							str(int(wind)) +',' + date + ','+ time))
				producer.send(mytopic, data)
				producer.send(mytopic, data)


def call_wind_api(lat, lon):
	str_url = API_STR
	url_json = urllib2.urlopen(str_url + str(lat) + "&lon="\
									+ str(lon) + "&FcstType=json")
	js_url = url_json.read()
	try:
		info = json.loads(js_url)
	except:
		info = None
	date_time = str(datetime.datetime.now()).replace(':', '')\
											.replace('-', '')
	date = date_time[0:8]
	time = date_time[9:15]
	wind = 0
	try:
		wind = info[u'currentobservation'][u'Winds']
	except:
		"""TODO: DECIDE COURSE OF ACTION FOR STATIONS THAT DONT
			RESPOND"""
		pass
	try:
		wind = int(wind)
	except:
		wind = 0
	data = (str(str(lon) + ',' + str(lat) + ',' + str(wind)\
								+ ',' + date + ',' + time))
	producer.send(mytopic, data)
	producer.send(mytopic, data)
	simulate(float(lat), float(lon), wind, date, time)


def main():
	with open('all_stations.json') as data_file:
		stations = json.load(data_file)
	get_stations(stations)


if __name__ == '__main__':
	main()
