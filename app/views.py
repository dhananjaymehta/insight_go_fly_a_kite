from app import app
from flask import render_template
from flask import request, jsonify
import redis, json, datetime, yaml
from ast import literal_eval
from handle_events import Surrounding_Listener
from elasticsearch import Elasticsearch


with open("settings-template.yaml", 'r') as stream:
	try:
		SETTINGS = yaml.load(stream)
	except yaml.YAMLError as exc:
		print(exc)


es = Elasticsearch([SETTINGS["ES_IP"]], http_auth=(SETTINGS["ES_USER_NAME"],\
					 			SETTINGS["ES_PASSWORD"]), verify_certs=False)
redis_server = SETTINGS["REDIS_IP"]
r = redis.StrictRedis(host=redis_server, port=6379, db=0)


@app.route('/')
@app.route('/index')
def index():
	user = { 'nickname': 'Miguel' } # fake user
	mylist = [1, 2, 3, 4]
	outdict = {}
	return render_template("index.html", title = 'Home')


@app.route('/score')
def get_surrounding():
	client = Surrounding_Listener(r, ['load_surrounding'])
	lon = request.args.get("lon")
	lat = request.args.get("lat")
	around = client.work([float(lat),float(lon)])
	return json.dumps(around)


@app.route('/closest')
def get_closest():
	# also get if in season and season list and gradient
	client = Surrounding_Listener(r, ['load_surrounding'])
	lon = request.args.get("lon")
	lat = request.args.get("lat")
	around = client.work_around([float(lat),float(lon)])
	return json.dumps(around)


@app.route('/quickspot')
def get_best():
	client = Surrounding_Listener(r, ['load_surrounding'])
	lon = request.args.get("lon")
	lat = request.args.get("lat")
	radius = request.args.get("radius")
	around = client.get_max([float(lat),float(lon)], radius)
	return json.dumps(around)


@app.route("/email")
def email_post():
	return render_template("emailop.html")


@app.route('/email')
def email():
	return render_template("email.html")


@app.route('/realtime')
def realtime():
	return render_template("realtime.html")


@app.route('/slider')
def slider():
	return render_template("slider.html")


@app.route('/regions')
def regions():
	q={"query": {"match_all": {}}}
	a = es.search(index="circles", doc_type="data", body=q, size=158)["hits"]["hits"]
	arr = [{"shape":a[i]["_source"]["shape"], "seasons":a[i]["_source"]["seasons"]} for i in range(0, len(a))]
 	return render_template("regions.html", data=arr)
