import os, sys, json, urllib2, random
import pylab as pl
from kafka import KafkaConsumer, KafkaProducer
import datetime, subprocess, get_wind

def main():
	with open('stations_1.json') as data_file:
		stations = json.load(data_file)
	# for i in range(0, 1000):
	get_wind.get_stations(stations)

if __name__ == '__main__':
	main()
