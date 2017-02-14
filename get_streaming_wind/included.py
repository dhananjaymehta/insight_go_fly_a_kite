import os, sys, json, urllib2, random
import station_dict_str

master_dict = {}
folder = []
for year in ['2007', '2008', '2009','2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017']:
	for month in ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']:
		if year >'2007' and year<'2017':
			folder.append(year+month+'station.txt')
		elif year is '2007' and month > '05':
			folder.append(year+month+'station.txt')
		elif year is '2017' and month <'02':
			folder.append(year+month+'station.txt')

for fyle in folder:
	text = open(fyle, 'r')
	d = station_dict_str.getDict(fyle)
	master_dict = dict(master_dict.items()+d.items())

size = len(master_dict.keys())/4
dict1 = dict(master_dict.items()[0:(size)])
dict2 = dict(master_dict.items()[size:(2*size)])
dict3 = dict(master_dict.items()[(2*size):(3*size)])
dict4 = dict(master_dict.items()[(3*size):])

with open('stations_1.json', 'w') as fp:
    json.dump(dict1, fp)

with open('stations_2.json', 'w') as fp:
    json.dump(dict2, fp)

with open('stations_3.json', 'w') as fp:
    json.dump(dict3, fp)

with open('stations_4.json', 'w') as fp:
    json.dump(dict4, fp)
