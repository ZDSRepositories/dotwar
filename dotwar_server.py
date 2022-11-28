import datetime

import bottle

import dotwar_classes
from bottle import run, route, request
import os, sys, json

"""
Implemented endpoints:
 /games *
 /game/<name>/status
 /game/<name>/scan
 /game/<name>/event_log, /game/<name>/summary
 /game/<name>/agenda?vessel=&authcode=
To do:
 /add_order?vessel=&authcode=&order={"task":"burn","args":{"a":[3d acceleration]}},"time":ISO date string}
 /delete_order?vessel=&authcode=&order_id=
 /request.......
 /parse?query=
 
"""
def load_config(directory=sys.path[0]):
    if os.path.exists(os.path.join(directory, "config.json")):
        config_file=open("config.json", "r")
        config=json.load(config_file)
        config_file.close()
        return config
    else:
        return {
            "server_addr":"localhost",
            "server_port":80,
            "dir":directory,
            "game_dir":directory,
            "welcome":"Welcome to the myrmidon/dotwar test server!"
        }

def get_game_list(directory = sys.path[0]):
    files = os.listdir(directory)
    games = []
    for file in files:
        if file.startswith("system.") and file.endswith(".json"):
            games.append(file.split(".")[1])
    return games

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

config=load_config(sys.path[0])

@route('/')
def hello_world(config=config):
    return config["welcome"]+"""<br>
    Running games:<br>"""+"<br> ".join(get_game_list())+"""<hr>"""

@route('/games')
def games():
    game_list = get_game_list()
    html="<br>".join(game_list)
    pretty="\n".join(game_list)
    return {"ok":True, "html":html, "pretty":pretty, "games":game_list}

@route('/game/<name>')
@route('/game/<name>/')
@route('/game/<name>/status')
@route('/game/<name>/status/')
def game_status(name, config=config):
    g = dotwar_classes.Game(0, name, config["game_dir"])
    q = request.query
    ret = {"ok":True, "game":None}
    g.load()
    g_json = g.as_json()["game"]
    ret["game"] = g_json
    if ("html" in q) and valid_json(q.html) and json.loads(q.html):
        return "<br>".join(["Game '"+name+"' status:",
                            "Created on: "+g_json["created_on"] + " ("+datetime.datetime.fromisoformat(g_json["created_on"]).strftime("%b %d %Y, %X")+")",
                            "System time: "+g_json["system_time"] + " ("+datetime.datetime.fromisoformat(g_json["system_time"]).strftime("%b %d %Y, %X")+")"
                            ])
    return ret

@route("/game/<name>/scan")
def scan(name):
    g=dotwar_classes.Game(0, name, config["game_dir"])
    g.load()
    entities=g.as_json()["entities"]

    for entity in entities:
        for k in ["pending", "authcode"]:
            try:
                del entity[k]
            except:
                print("key error on", k)

    if ("filter" in request.query) and valid_json(request.query.filter):
        filters = json.loads(request.query.filter)
        entities = list(filter(lambda entity: all([entity[k] == filters[k] for k in filters]), entities))
    elif ("filter" in request.query) and not valid_json(request.query.filter):
        return {"ok":False, "msg":"invalid JSON provided in 'filter'"}

    if ("html" in request.query) and valid_json(request.query.html) and json.loads(request.query.html):
        page =["<pre>NAME\tTYPE\tCAPTAIN\tPOSITION\t\tHEADING\t\t\tACCELERATION"]
        for entity in entities:
            desc = "&#9;".join([str(attr) for attr in
                              [entity["name"],
                               entity["type"],
                               (entity["captain"] if entity["captain"] else "----"),
                               " ".join([format(value, ".3f") for value in (entity["r"])]),
                               " ".join([format(value, ".3f") for value in (entity["v"])]),
                               " ".join([format(value, ".3f") for value in (entity["a"])])]])
            page.append(desc)
        page.append("</pre>")
        return "<br/>".join(page)
    elif ("html" in request.query) and not valid_json(request.query.html):
        return {"ok": False, "msg": "invalid JSON provided in 'html'"}
    else:
        return {"ok": True, "entities": entities}

@route("/game/<name>/event_log")
@route("/game/<name>/summary")
def summary(name, config=config):
    g = dotwar_classes.Game(0, name, config["game_dir"])
    g.load()
    q = request.query
    q.start, q.end = q.start.strip(), q.end.strip()
    start = datetime.datetime.fromisoformat(q.start) if (q.start and valid_json(q.start)) else datetime.datetime.fromtimestamp(0)  # the epoch
    end = datetime.datetime.fromisoformat(q.end) if (q.end and valid_datetime(q.end)) else g.system["game"]["system_time"]

    events = g.event_log(start, end)

    if ("start" in q and "end" in q) and not (valid_datetime(q.start) and valid_datetime(q.end)):
        return {"ok":False, "msg":"if used, start and end must be ISO datetime strings"}

    if "html" in q and valid_json(q.html) and json.loads(q.html):
        page = ["<pre>Events between "+(q.start if q.start else "system start")+" and "+(q.end if q.end else "current time:")]
        for event in events:
            time = datetime.datetime.fromisoformat(event["time"]).strftime("%b %d %Y, %X")
            desc=""
            abbr =""
            if event["type"] == "capture":
                desc = ["vessel", event["args"]["attacker"], "captured", event["args"]["planet"]]
                abbr = "  [ATK] "
            elif event["type"] == "defense":
                desc = ["vessel", event["args"]["defender"], "destroyed vessel", event["args"]["victim"]]
                abbr = "  [DEF] "
            elif event["type"] == "burn":
                desc = ["vessel", event["args"]["vessel"], "started burn", str(event["args"]["a"]), "while at coords",
                        str([float(format(value, ".3f")) for value in event["args"]["position"]])]
                abbr = "  [NAV] "
            desc = abbr.join([time, " ".join(desc)])
            page.append(desc)

        return "<br/>".join(page)

    else:
        return {"ok":True, "events":events}

@route("/game/<name>/agenda")
def agenda(name):
    g = dotwar_classes.Game(0, name, config["game_dir"])
    g.load()
    q = request.query
    if not ("vessel" in q):
        return {"ok":False, "msg":"Please provide a spacecraft name as 'vessel' in query string."}
    if not ("authcode" in q):
        return {"ok":False, "msg":"Please provide an authorization code as 'authcode' in query string."}
    vessel = g.get_entity(q.vessel)
    if not vessel: return {"ok":False, "msg":"No vessel named '"+q.vessel+"'."}
    if not ("authcode" in vessel): return {"ok":False, "msg":"Vessel has no authcode."}
    if (vessel["authcode"] != q.authcode):
        bottle.response.status = 403
        return {"ok":False, "msg":"Not authorized. "+q.authcode+" is not this vessel's authcode."}
    if ("html" in q) and valid_json(q.html) and json.loads(q.html):
        page = ["<pre>Pending orders for vessel " + vessel["name"]+":"]
        for order in vessel["pending"]:
            page.append("at {}: burn [{:.3f} {:.3f} {:.3f}] (order ID: {})".format(order["time"].strftime("%X %p on %A, %b %d, %Y"),*order["args"]["a"], order["order_id"])) # formerly format "%b %d %Y, %X"
            page = "<br>".join(page)
            return page

    else:
        for order in vessel["pending"]:
            order["time"] = order["time"].isoformat()
        return {"ok":True, "agenda":vessel["pending"]}

@route("/game/<name>/add_order")
def add_order(name):
    g = dotwar_classes.Game(0, name, config["game_dir"])
    g.load()
    q = request.query
    if not ("vessel" in q):
        return {"ok": False, "msg": "Please provide a spacecraft name as 'vessel' in query string."}
    if not ("authcode" in q):
        return {"ok": False, "msg": "Please provide an authorization code as 'authcode' in query string."}
    vessel = g.get_entity(q.vessel)
    if not vessel: return {"ok": False, "msg": "No vessel named '" + q.vessel + "'."}
    if not ("authcode" in vessel): return {"ok": False, "msg": "Vessel has no authcode."}
    if vessel["authcode"] != q.authcode:
        bottle.response.status = 403
        return {"ok": False, "msg": "Not authorized. " + q.authcode + " is not this vessel's authcode."}
    if not "order" in q:
        return {"ok":False, "msg":"Please give an order as 'order=order JSON' in query string."}
    if valid_json(q.order):
        order = json.loads(q.order)
    else:
        return {"ok":False, "msg": "Invalid JSON in order."}
    allowed_keys = ["task", "args", "time"]
    order = dict([allowed_keys, [order[key] for key in allowed_keys]])
    g.add_order(q.vessel, task=order["task"], args=order["args"], time=order["time"])
    g.save()


print(get_game_list())
run(host=config["server_addr"], port=config["server_port"], debug=True)

