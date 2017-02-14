import json, datetime
import threading
from ast import literal_eval
from datetime import datetime
from elasticsearch import Elasticsearch
import handle_events

with open("settings-template.yaml", 'r') as stream:
	try:
		SETTINGS = yaml.load(stream)
	except yaml.YAMLError as exc:
		print(exc)

es = Elasticsearch([SETTINGS["ES_IP"]], http_auth=(SETTINGS["ES_USER_NAME"],\
					 			SETTINGS["ES_PASS"]), verify_certs=False)

def get_regions_a():
	all_loc = json.load(open("all_stations.json", "r"))
	loc_dict = {}
	regions = []
	for key in all_loc:
		print "KEY: ", all_loc[key][0], all_loc[key][1]
		loc_dict[(all_loc[key][0], all_loc[key][1])] = get_all_seasons(all_loc[key][0], all_loc[key][1])
	return loc_dict

def get_regions_b(loc_dict):
	regions = []
	for loc in loc_dict.keys():
		if loc in loc_dict:
			lat, lon = loc
			query1 = { "query": {"bool" : {"must" : {"match_all":{}},"filter" : {"geo_distance" : {
					                    "distance" : "80km","location" : {"lat" : lat,"lon" : lon}}}}}}
			try:
				dmy = es.search(index="batch_data", doc_type="data", body=query1, size=1)["hits"]["hits"][0]["_source"]				
				print "DMY: ", dmy
				d = dmy["day"]
				m = dmy["month"]
				y = dmy["year"]
				query = { "query": {
					        "bool" : {
					            "must" : [
					            		{"match":{"day":d}},
					            		{"match":{"month":m}},
					            		{"match":{"year":y}}
					            ],
					            "filter" : {
					                "geo_distance" : {
						                    "distance" : "80km",
						                    "location" : {
						                        "lat" : lat,
						                        "lon" : lon
										                 }
									                }
									        }
										}
									}
						}
				neighbors = es.search(index="batch_data", doc_type="data", body=query, size=200)['hits']['hits']
				r = {}
				for n in neighbors:
					lat_n = n["_source"]["location"]["lat"]
					lon_n = n["_source"]["location"]["lon"]
					print "lat: ", lat_n, " lon: ", lon_n
					try:
						value = loc_dict[(lat_n, lon_n)]
						if (lat, lon) in r.keys():
							r[(lat, lon)] = r[(lat, lon)].append(value)
						else:
							r[(lat, lon)] = [value]
						del loc_dict[(lat_n,lon_n)]
					except:
						pass
				regions.append(r)
			except IndexError as e:
				if e.message != "list index out of range":
					raise
				else:
					pass
	return regions

def make_shapes(regions):
	p = "polygon"
	polygons = []
	i = 0
	for r in regions:
		i += 1
		polys = []
		out_season = [0] * 12
		for key in r:
			for j in range(0, 12):
				if r[key]:
					out_season[j] += 1
			polys.append(str(key[0])+", "+str(key[1]))
		if len(r.keys()) > 0:
			polygons.append({"shape":polys, "season":out_season})
	return polygons

regions = get_regions()
polygons = make_shapes(regions)
for p in polygons:
	es.index(index="polygons", doc_type="data", body=p)





