import datetime

import bottle

import dotwar_classes
from bottle import run, route, request, hook, response, HTTPResponse
import os
import sys
import json
# import urllib.parse
from urllib.parse import unquote

# Implemented endpoints:
#  /games *
#  /game/<name>/status
#  /game/<name>/scan
#  /game/<name>/event_log, /game/<name>/summary
#  /game/<name>/agenda?vessel=&authcode=
#  /add_order?vessel=&authcode=&order={"task":"burn","args":{"a":[3d acceleration]}},"time":ISO date string}
# To do:
#  TODO: /game/<name>/delete_order?vessel=&authcode=&order_id=
#  TODO: /play/<name> returns the client, setup for the specified game
#  TODO: Convert all endpoints from GET to POST


def load_config(directory=sys.path[0]):
	if os.path.exists(os.path.join(directory, "config.json")):
		config_file = open("config.json", "r")
		loaded_config = json.load(config_file)
		config_file.close()
		return loaded_config
	else:
		return {
			"server_addr": "localhost",
			"server_port": 80,
			"dir": directory,
			"game_dir": directory,
			"static_dir": os.path.join(directory, "static"),
			"debug": True,
			"welcome": "Welcome to the myrmidon/dotwar test server!"
		}


global_config = load_config(sys.path[0])


def get_game_list():
	files = os.listdir(global_config["game_dir"])
	game_list = []
	for file in files:
		if file.startswith("system.") and file.endswith(".json"):
			game_list.append(file.split(".")[1])
	return game_list


def valid_json(json_string):
	try:
		json.loads(json_string)
	except json.decoder.JSONDecodeError:
		return False
	return True


def valid_datetime(iso_string):
	try:
		datetime.datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
	except:
		return False
	return True

def select_err(err, use_html):
	return err if use_html else {"ok": False, "msg":err}

def generate_table(headers, data_rows):
	# headers: list of table headers.
	# data_rows: list of rows of the table, each row a list of individual elements
	table_rows = ["<tr>" + ("".join(["<th>" + header + "</th>" for header in headers])) + "</tr>"]
	for data_row in data_rows:
		table_rows.append(
			"<pre>" + (
				"".join(["<td>" + element + "</td>" for element in data_row])
			) + "</tr>"
		)
	return "<table>" + "".join(table_rows) + "</table>"


def assemble_client(name):
	client_html = ""  # client template
	with open(os.path.join(global_config["static_dir"], "client.html")) as client_file:
		client_html = "".join(client_file.readlines())
	client_html = client_html.replace("{{GAMENAME}}", name)
	return client_html


def try_authorize_vessel(game: dotwar_classes.Game, vessel_name: str, authcode: str):
	try:
		vessel = game.get_authorized_entity(vessel_name, authcode)
	except LookupError as e:
		bottle.response.status = 404
		return {"ok": False, "msg": str(e)}
	except ValueError as e:
		return {"ok": False, "msg": str(e)}
	except PermissionError as e:
		bottle.response.status = 403
		return {"ok": False, "msg": str(e)}

	return vessel

# route for main page. not API. not POST.
@route('/', method="GET")
def hello_world():
	return global_config["welcome"] + "<br>Running games:<br>" + "<br> ".join(
		[f"<a href='/play/{game}'>{game}</a>" for game in get_game_list()]) + """<hr>"""


# route to retrieve client. not API. not POST.
@route("/play/<name>")
def play(name):
	if name not in get_game_list():
		bottle.response.status = 404
		return f"Couldn't find game <code>{name}</code>."

	return assemble_client(name)


@route('/games', method="POST")
def games():
	game_list = get_game_list()
	return {"ok": True, "games": game_list}


@route('/game/<name>', method="POST")
@route('/game/<name>/', method="POST")
@route('/game/<name>/status', method="POST")
@route('/game/<name>/status/', method="POST")
def game_status(name):
	game = update_to_now(name)
	query = request.POST

	ret = {"ok": True, "game": None}

	g_json = game.system_as_json()["game"]
	ret["game"] = g_json
	if ("html" in query) and valid_json(query.html) and json.loads(query.html):
		return "<br>".join(["Game '" + name + "' status:",
							"Created on: " + g_json["created_on"] + " (" + datetime.datetime.fromisoformat(
								g_json["created_on"]).strftime("%b %d %Y, %X") + ")",
							"System time: " + g_json["system_time"] + " (" + datetime.datetime.fromisoformat(
								g_json["system_time"]).strftime("%b %d %Y, %X") + ")"
							])
	return ret


@route("/game/<name>/scan", method="POST")
def scan(name):
	game = update_to_now(name)
	json_entities = game.system_as_json()["entities"]
	query = request.POST
	print("HTTP?", query.html)

	for entity in json_entities:
		for culled_attribute in ["pending", "authcode"]:
			try:
				del entity[culled_attribute]
			except:
				pass

	if ("filter" in query) and valid_json(query.filter):
		filters = json.loads(query.filter)
		json_entities = list(filter(lambda json_entity: all([json_entity[k] == filters[k] for k in filters]), json_entities))
	elif ("filter" in query) and not valid_json(query.filter):
		return {"ok": False, "msg": "invalid JSON provided in 'filter'"}

	if ("html" in query) and valid_json(query.html) and json.loads(query.html):
		rows = [[json_entity["name"], json_entity["type"], (json_entity["captain"] if json_entity["captain"] else "-----"),
				f"<{json_entity['r'][0]:.3f} {json_entity['r'][1]:.3f} {json_entity['r'][2]:.3f}>",
				f"<{json_entity['v'][0]:.3f} {json_entity['v'][1]:.3f} {json_entity['v'][2]:.3f}>",
				f"<{json_entity['a'][0]:.3f} {json_entity['a'][1]:.3f} {json_entity['a'][2]:.3f}>",
				["Defenders", "Attackers", "Itself"][json_entity["team"]]
				] for json_entity in json_entities]
		table = generate_table(["NAME", "TYPE", "CAPTAIN", "POSITION", "HEADING", "ACCELERATION", "ALLEGIANCE"], rows)
		style_tag = """<style>
table {
	font-family: Roboto, sans-serif;
	border-collapse: collapse;
}

td, th {
	font-size: 14px;
	/*border: 1px solid #000000;*/
	text-align: left;
	padding: 5px;
}

tr:nth-child(even) {
	background-color: #dddddd;
}
</style>"""
		page = style_tag + table
		return page
	elif ("html" in query) and not valid_json(query.html):
		return {"ok": False, "msg": "invalid JSON provided in 'html'"}
	else:
		return {"ok": True, "entities": json_entities}


@route("/game/<name>/event_log", method="POST")
@route("/game/<name>/summary", method="POST")
def summary(name):
	game = update_to_now(name)
	query = request.POST

	query.start, query.end = query.start.strip(), query.end.strip()

	start = datetime.datetime.fromisoformat(query.start) if (
			query.start and valid_json(query.start)) else datetime.datetime.fromtimestamp(0)  # the epoch
	end = datetime.datetime.fromisoformat(query.end) if (
			query.end and valid_datetime(query.end)) else game.get_system_time()

	events = game.get_event_log(start, end)

	if ("start" in query and "end" in query) and not (valid_datetime(query.start) and valid_datetime(query.end)):
		return {"ok": False, "msg": "if used, start and end must be ISO datetime strings"}
	if "html" in query and valid_json(query.html) and json.loads(query.html):
		page = ["<pre>Events between " + (query.start if query.start else "system start") + " and " + (
			query.end if query.end else "current time:")]
		for event in events:
			time = datetime.datetime.fromisoformat(event["time"]).strftime("%b %d %Y, %X")
			desc = ""
			abbr = ""
			if event["type"] == "capture":
				desc = ["vessel", event["args"]["attacker"], "captured", event["args"]["planet"]]
				abbr = "  [ATK] "
			elif event["type"] == "defense":
				desc = ["vessel", event["args"]["defender"], "destroyed vessel", event["args"]["victim"], "while at coords", str([float(format(value, ".3f")) for value in event["args"]["defender_kinematics"]["r"]])]
				abbr = "  [DEF] "
			elif event["type"] == "burn":
				desc = ["vessel", event["args"]["vessel"], "started burn", str(event["args"]["a"]), "while at coords",
						str([float(format(value, ".3f")) for value in event["args"]["kinematics"]["r"]])]
				abbr = "  [NAV] "
			desc = abbr.join([time, " ".join(desc)])
			page.append(desc)
		return "<br/>".join(page)

	else:
		return {"ok": True, "events": events}


@route("/game/<name>/agenda", method="POST")
def agenda(name):
	game = update_to_now(name)
	query = request.POST

	if "vessel" not in query:
		return {"ok": False, "msg": "Please provide a spacecraft name as 'vessel' in query string."}

	if "authcode" not in query:
		return {"ok": False, "msg": "Please provide an authorization code as 'authcode' in query string."}

	auth = try_authorize_vessel(game, query.vessel, query.authcode)

	if type(auth) is dotwar_classes.Entity:
		vessel = auth
	else:
		return auth

	if ("html" in query) and valid_json(query.html) and json.loads(query.html):
		page = [f"<pre>Pending orders for vessel {vessel.name}:"]
		for order in vessel.pending:
			page.append("at {}: burn [{:.3f} {:.3f} {:.3f}] ; order ID: {}"
						.format(order["time"].strftime("%I:%M %p on %A, %b %d, %Y"),
								*order["args"]["a"], order["order_id"]
								)
						)  # formerly format "%b %d %Y, %X"
		page = "<br>".join(page)
		return page
	else:
		for order in vessel.pending:
			order["time"] = order["time"].isoformat()
		return {"ok": True, "agenda": vessel.pending}


@route("/game/<name>/add_order", method="POST")
def add_order(name):
	game = dotwar_classes.Game(name, global_config["game_dir"])
	query = request.POST

	if "vessel" not in query:
		return select_err("Please provide a spacecraft name as 'vessel' in query string.", query.html)

	if "authcode" not in query:
		return select_err("Please provide an authorization code as 'authcode' in query string.", query.html)

	auth = try_authorize_vessel(game, query.vessel, query.authcode)

	if type(auth) is dotwar_classes.Entity:
		vessel = auth
	else:
		return select_err(auth["msg"], query.html)

	if valid_json(query.order):
		order = json.loads(query.order)
		print(f"ORDER JSON: {order}")
	else:
		return select_err(f"Invalid JSON in order {query.order}", query.html)

	if order["time"] == None:
		order["time"] = datetime.datetime.now()
	elif "interval" in order:
		if type(order["interval"] in [int, float]):
			print(f"order time is at an interval of {order['time']} seconds")
			order["time"] = datetime.datetime.now() + datetime.timedelta(seconds=order["time"])
			print(f"set order time to {order['time'].isoformat()}")
		else:
			return {"ok": False, "msg": f"Invalid interval parameter: type must be int or float, not {type(order['interval'])}", "input": query.order}
	elif "time" in order:
		if valid_datetime(order["time"]):
			order["time"] = datetime.datetime.fromisoformat(order["time"])
		else:
			return {"ok": False, "msg": "Invalid time parameter.", "input": query.order}
	else:
		print("NO TIME SPECIFIED IN ORDER, SETTING TO CURRENT TIME")
		order["time"] = datetime.datetime.now()

	order["args"]["a"] = [float(e) for e in order["args"]["a"]]
	order_id = vessel.add_order(task=order["task"], args=order["args"], time=order["time"])
	game.save()
	update_to_now(name, game)

	if "html" in query and valid_json(query.html) and json.loads(query.html):
		return f"Order <code>{order['task']} {order['args']} at {order['time']:%I:%M %p on %A, %b %d, %Y}</code> given to vessel {query.vessel} with order ID {order_id}."
	else:
		return {"ok": True, "vessel": query.vessel, "added_id": order_id}


@route("/game/<name>/delete_order", method="POST")
def delete_order(name):
	# required keys: vessel, order_id, authcode
	# optional keys: html

	game = update_to_now(name)
	query = request.POST

	print("in delete_order, headers =", dict(query))

	if not ("vessel" in query and "authcode" in query and "order_id" in query):
		return {"ok": False, "msg": "vessel, order_id, and authcode are required"}

	order_id = json.loads(query.order_id)
	try:
		order_id = int(order_id)
	except:
		return {"ok": False, "msg": f"order_id must be an integer, but is {query.order_id}"}

	auth = try_authorize_vessel(game, query.vessel, query.authcode)

	if type(auth) is dotwar_classes.Entity:
		vessel = auth
	else:
		return auth

	if not vessel.get_order(order_id):
		return {"ok": False, "msg": f"no pending order #{query.order_id} for vessel {query.vessel}"}

	# all tests passed:
	vessel.clear_order(order_id)
	pending_count = len(vessel.get_pending())
	game.save()

	if "html" in query and bool(json.loads(query.html)):
		return {"ok": True, "removed_id": order_id, "pending_count": pending_count}
	else:
		return f"Removed order with ID {order_id} from vessel {query.vessel}. {pending_count} order(s) pending."


# @route("/game/<name>/update_simulation_debug")
def update_to_now(name=None, game: dotwar_classes.Game = None):
	game = dotwar_classes.Game(name, global_config["game_dir"]) if game is None else game
	old = game.get_system_time()
	now = datetime.datetime.now()
	print("simulation will be updated from {} to {}, delta of {}".format(old, now, (now - old)), "...")
	game.update_to(now)
	new = game.get_system_time()
	game.save()
	print("simulation updated to " + new.isoformat() + ",delta of {}".format(new - old))
	return game

cors_headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    # 'Access-Control-Allow-Headers': 'X-Token, ...',
    # 'Access-Control-Expose-Headers': 'X-My-Custom-Header, ...',
    # 'Access-Control-Max-Age': '86400',
    # 'Access-Control-Allow-Credentials': 'true',
}

@hook('before_request')
def handle_options():
    if request.method == 'OPTIONS':
        # Bypass request routing and immediately return a response
        raise HTTPResponse(headers=cors_headers)

@hook('after_request')
def enable_cors():
    for key, value in cors_headers.items():
       response.set_header(key, value)


print("[INFO] Detected games:", get_game_list())
print("[INFO] __name__ at startup:", __name__)
application = bottle.default_app()
print("[INFO] Created default_app")

if __name__ == "__main__":
	print("[INFO] Starting dev server on", global_config["server_addr"], global_config["server_port"], "with debug",
		["disabled", "enabled"][global_config["debug"]] + "...")
	run(app=application, host=global_config["server_addr"], port=global_config["server_port"],
		debug=global_config["debug"])
else:
	print("[INFO] Not in __main__, continuing with default_app only instantiated")
