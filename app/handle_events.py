import redis, json, datetime
import threading, yaml
from ast import literal_eval
from datetime import datetime
from elasticsearch import Elasticsearch


with open("settings-template.yaml", 'r') as stream:
	try:
		SETTINGS = yaml.load(stream)
	except yaml.YAMLError as exc:
		print(exc)


class Surrounding_Listener(threading.Thread):
	def __init__(self, r, channels):
		threading.Thread.__init__(self)
		self.r = r
		self.pubsub = self.r.pubsub()
		self.pubsub.subscribe(channels)

	def work(self, item):
		# add all markers within 5 miles
		lat = item[0]
		lon = item[1]
		surrounding = self.r.georadius("all_loc", lon, lat, 5, unit="mi")
		out = []
		i=0
		for loc in surrounding:
			val = self.r.get(loc)
			pos = self.r.geopos("all_loc", loc)
			if val is not None:
				val = eval(val)
				out.append({"value": val, 
							"longitude": pos[0][0],
							"latitude": pos[0][1]})
				i+=1
		return out


	def work_around(self, item):
		lat = item[0]
		lon = item[1]
		closest = self.r.georadius("all_loc", lon, lat, .5, unit="mi")
		if len(closest)>0:
			val = eval(self.r.get(closest[0]))
			pos = self.r.geopos("all_loc", closest[0])
			season = get_season(pos[0][0], pos[0][1], int(datetime.now().strftime("%m")))
			gradient = get_gradient(pos[0][0], pos[0][1], val[0])
			if val is not None:
				out = {"value" : val, 
						"longitude": pos[0][0],
						"latitude": pos[0][1],
						"gradient": gradient,
						"season": season}
			else:
				{"value": None,
				"longitude": None,
				"latitude": None,
				"gradient": False, 
				"season": False}
			return out
		else:
			return {}

	def get_max(self, ll, radius):
		lat = ll[0]
		lon = ll[1]
		closest = self.r.georadius("all_loc", lon, lat, radius, unit="mi")
		if len(closest) > 0:
			max_w = (0.0, 0.0)
			ll_max = None
			for loc in closest:
				val = eval(self.r.get(loc))
				if val[1] > max_w[1]:
					max_w = val
					ll_max = self.r.geopos("all_loc", loc)
			season = get_season(ll_max[0][0], ll_max[0][1], int(datetime.now().strftime("%m")))
			gradient = get_gradient(ll_max[0][0], ll_max[0][1], val[0])
			return {"value" : max_w,
					"longitude" : ll_max[0][0],
					"latitude" : ll_max[0][1],
					"gradient": gradient,
					"season": season
					}
		else:
			return {}


def get_season(lat, lon, month):
	es = Elasticsearch(['52.33.3.123'], http_auth=('elastic',\
					 			'changeme'), verify_certs=False)
	# month = datetime.datetime.now().strftime("%m")
	stations = json.load(open("all_stations.json", "r"))
	if [lat,lon] in stations.values():
		all_good_days = { "query":                                                              
					        {"bool" : 
					            {"must": [
					                      {"range": {"maxWs":  {"gte" : 15}}},
								          {"match": {"month": str(month)}}
					                     ],
					                "filter": {"geo_distance": 
					                                {"distance": "1km",
					                                 "location": {"lat" : lat,"lon" : lon}
					                                }
					                            }
					            }
					        }
						}
		all_days = { "query":                                                              
					        {"bool" : 
					            {"must": 
								    {"match": {"month": str(month)}},
					                "filter": {"geo_distance": 
					                                {"distance": "1km",
					                                 "location": {"lat" : lat,"lon" : lon}
					                                }
					                            }
					            }
					        }
					}
		tot_gd = es.search(index='batch_data', doc_type="data", body=all_good_days, size=0)["hits"]["total"]
		tot = es.search(index='batch_data', doc_type="data", body=all_days, size=0)["hits"]["total"]
		
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
	seasons = [get_season(lat, lon, i) for i in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]]
	return seasons


def get_gradient(lon, lat, curr_w):
	es = Elasticsearch([SETTINGS["ES_IP"]], http_auth=(SETTINGS["ES_USER_NAME",\
			 			SETTINGS["ES_PASS"]), verify_certs=False)
	hour = datetime.now().hour
	es_val = { "query":                                                                     
    			{"bool" : 
            		{"must" : 
                    	{"range" : {"hour":{"gte":str(hour-1), "lte":str(hour)}}},
            			"filter" : {"geo_distance" : 
                                       {"distance" : "5km",
                                        "location" : {"lat" : lat,"lon" : lon}
                                        }
                                    }
            		}
    			}
			}
	wind = es.search(index='stream_data',doc_type="data", body=es_val, size=1)["hits"]["hits"][0]["_source"]["wind"]
	print "\n WIND \n", wind
	return curr_w - wind > 0

	

	def run(self):
		for item in self.pubsub.listen():
			if item['data'] == "KILL":
				self.pubsub.unsubscribe()
				print self, "unsubscribed and finished"
				break
			else:
				self.work(item)

if __name__ == "__main__":
	redis_server = SETTINGS["REDIS_IP"]
	redis_session = redis.StrictRedis(host=redis_server, port=6379, db=0)
	client = Surrounding_Listener(redis_server, ['load_surrounding'])
	client.start()