import json, datetime, yaml
import threading
from ast import literal_eval
from datetime import datetime
from elasticsearch import Elasticsearch
import handle_events
import numpy as np
from geopy.distance import vincenty

with open("settings-template.yaml", 'r') as stream:
	try:
		SETTINGS = yaml.load(stream)
	except yaml.YAMLError as exc:
		print(exc)

es = Elasticsearch([SETTINGS["ES_IP"]], http_auth=(SETTINGS["ES_USER_NAME"],
					 			SETTINGS["ES_PASSWORD"]), verify_certs=False)


def get_season(lat, lon, month):
	stations = json.load(open("all_stations.json", "r"))
	if [lat, lon] in stations.values():
		all_good_days = {"query":                                                              
					        {"bool" : 
					            {"must": [
					                      {"range": {"maxWs":  {"gte": 15}}},
								          {"match": {"month": str(month)}}
					                     ],
					                "filter": {"geo_distance":
					                                {"distance": "1km",
					                                 "location": {"lat": lat,"lon": lon}
					                                }
					                            }
					            }
					        }
						}
		all_days = {"query":                                                              
					        {"bool": 
					            {"must":
								    {"match": {"month": str(month)}},
					                "filter": {"geo_distance":
					                                {"distance": "1km",
					                                 "location": {"lat": lat,"lon": lon}
					                                }
					                            }
					            }
					        }
					}
		tot_gd = es.search(index='batch_data', doc_type="data", body=all_good_days,
																size=0)["hits"]["total"]
		tot = es.search(index='batch_data', doc_type="data", body=all_days,
															 size=0)["hits"]["total"]
		try:
			per = float(tot_gd) / tot
		except ZeroDivisionError as e:
			if e.message != "float division by zero":
				raise
			else:
				per = 0
		if per >= 0.4:
			return True
		else:
			return False
	else:
		return None


def get_all_seasons(lat, lon):
	seasons = [get_season(lat, lon, i) for i in ["01", "02", "03", "04", "05", "06", "07",
															"08", "09", "10", "11", "12"]]
	return seasons


def get_regions_a():
	all_loc = json.load(open("all_stations.json", "r"))
	loc_dict = {}
	regions = []
	for key in all_loc:
		loc_dict[(all_loc[key][0], all_loc[key][1])] = get_all_seasons(all_loc[key][0],\
																		all_loc[key][1])
	return loc_dict


def within_radius(loc_dict):
	circles = {}
	i = 0
	for loc in loc_dict.keys():
		i += 1
		if loc in loc_dict:
			(lat, lon) = loc
			circles[(lat, lon)] = [loc_dict[(lat, lon)]]
			del loc_dict[loc]
			for locb in loc_dict.keys():
				(latb, lonb) = locb
				if vincenty(loc, locb).miles < 200:
					circles[(lat, lon)].append(loc_dict[(latb, lonb)])
					del loc_dict[locb]
	return circles


def reduce_circles(c):
	circles = {}
	for k in c:
		arrs = c[k]
		out = [0] * 12
		for year in arrs:
			for month in range(0, 12):
				if year[month]:
					out[month] += 1
		circles[k] = [float(out[x]) / len(arrs) for x in range(0, 12)]
	return circles


def write_2_circles(c):
	es = Elasticsearch([SETTINGS[ES_IP]], http_auth=(SETTINGS[ES_USER_NAME],
					 SETTINGS[ES_PASSWORD]), verify_certs=False)		
	for k in c:
		d = {"shape": k,
			 "seasons": c[k]}
		es.index(index='circles', doc_type='data', body=d)


get_regions_b(np.load("regions.npy").item())
