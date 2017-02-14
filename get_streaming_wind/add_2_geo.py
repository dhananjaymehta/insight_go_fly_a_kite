import redis, yaml


with open("settings-template.yaml", 'r') as stream:
	try:
		SETTINGS = yaml.load(stream)
	except yaml.YAMLError as exc:
		print(exc)


def add_locs(lat, lon, lat_range, lon_range):
	"""Adds the geoposition of the weather stations and simulated stations
		to redis"""
	redis_server = SETTINGS['REDIS_IP']
	redis_session = redis.StrictRedis(host=redis_server,\
							port=6379, db=0)
	redis_session.geoadd("all_loc", lon, lat, str(str(lon) + "," + str(lat)))
	for lat_i in lat_range:
		for lon_j in lon_range:
			redis_session.geoadd("all_loc", lon_j, lat_i, str(str(lon_j)\
											+ "," + str(lat_i)))


def delete_loc(lat, lon):
	"""Deletes station geoposition from redis"""
	redis_server = SETTINGS['REDIS_IP']
	redis_session = redis.StrictRedis(host=redis_server,\
							port=6379, db=0)
	redis_session.zrem("all_loc", str(str(lon), str(lat)))
