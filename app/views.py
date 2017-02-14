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
					 			SETTINGS["ES_PASS"]), verify_certs=False)
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



# @app.route('/seasons')
# def get_month():
# 	client = Surrounding_Listener(r, ['load_surrounding'])
# 	lon = request.args.get("lon")
# 	lat = request.args.get("lat")
# 	month = datetime.datetime.now().strftime("%m")
# 	around = client.get_regions([float(lat),float(lon)], month)
# 	if around:
# 		out = {"bool":"true"}
# 	else:
# 		out = {"bool": "false"}
# 	return around



@app.route("/email", methods=['POST'])
def email_post():
	emailid = request.form["emailid"]
	date = request.form["date"]
#email entered is in emailid and date selected in dropdown is in date variable respectively

	stmt = "SELECT * FROM email WHERE id=%s and date=%s"
	response = session.execute(stmt, parameters=[emailid, date])
	response_list = []
	for val in response:
		response_list.append(val)
	jsonresponse = [{"fname": x.fname, "lname": x.lname, "id": x.id, "message": x.message, "time": x.time} for x in response_list]
	return render_template("emailop.html", output=jsonresponse)

@app.route('/email')
def email():
	return render_template("email.html")

@app.route('/realtime')
def realtime():
	return render_template("realtime.html")

@app.route('/regions')
def regions():
	q={"query": {
       "match_all": {}
    			}
		}
	print "LALALAL"
	a = es.search(index="polygons", doc_type="data", body=q, size=841)["hits"]["hits"]
	arr = [{"shape":a[i]["_source"]["shape"], "season":a[i]["_source"]["season"]} for i in range(0, len(a))]
	print "ARRRR: ", arr
	# poly={"foo":"bar"}
	# print "poly: ", poly
 	return render_template("regions.html", data=arr)
