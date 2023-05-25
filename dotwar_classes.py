import copy
import os
import datetime
import json
import uuid
import numpy as np
import math

def dist(a, b):
	c = np.array(b) - np.array(a)
	return abs((c.dot(c)) ** (1 / 2))


def mag(a):
	#print(f"vector {a} of type {type(a)}")
	return np.sqrt(a.dot(a))


def datetime_decode_hook(obj):
	try:
		# print("decoding as datetime")
		return datetime.datetime.fromisoformat(obj)
	except:
		return datetime.datetime.fromisoformat(obj)

class team:
	SELF = -1
	DEFENDER = 0
	ATTACKER = 1

class Entity:
	def __init__(self,
				name: str,
				captain: str,
				r: np.array or list,
				v: np.array or list,
				a: np.array or list,
				entity_type: str,
				pending: list,
				team: int,
				created_on: datetime.datetime or str,
				authcode: str or None = None,
				captured: bool or None = None):
		self.name = name
		self.captain = captain
		self.r = r if type(r) is np.array else np.array(r)
		self.v = v if type(v) is np.array else np.array(v)
		self.a = a if type(a) is np.array else np.array(a)
		self.entity_type = entity_type
		self.pending = pending
		self.team = team
		self.created_on = created_on if type(created_on) is datetime.datetime\
			else datetime.datetime.fromisoformat(created_on)
		self.authcode = authcode
		self.captured = captured

	def get_pending(self):
		return self.pending

	def get_json_pending(self):
		pend_list = copy.deepcopy(self.get_pending())

		for order in pend_list:
			order["time"] = order["time"].isoformat()

		return pend_list

	def as_json(self):
		json_compatible = {
			"name": self.name,
			"captain": self.captain,
			"r": self.r.tolist(),
			"v": self.v.tolist(),
			"a": self.a.tolist(),
			"type": self.entity_type,
			"pending": self.get_json_pending(),  # <- can this be comprehended/lambda'd/mapped?
			"team": self.team,
			"created_on": self.created_on.isoformat(),
		}

		if type(self.authcode) is str:
			json_compatible["authcode"] = self.authcode

		if type(self.captured) is bool:
			json_compatible["captured"] = self.captured

		return json_compatible

	def add_order(self, task, args, time):
		# order example: {"task":"burn", args:{"a":[0, 20, 1]}, "time":datetime}
		order = {
			"task": task,
			"args": args,
			"time": datetime.datetime.fromisoformat(time) if type(time) is str else time
		}

		if task == "burn":
			if "a" not in args:
				raise Exception("Burn order creation missing 'a' in args")
			if any([(math.isnan(e) or math.isinf(e)) for e in args["a"]]):
				raise ValueError("NaN and Inf not allowed in acceleration")
		if not all([type(e) in [int, float] for e in args["a"]]):
			raise Exception(f"Acceleration must be a list of integers or floats, not {[type(e) for e in args['a']]}")

		order["order_id"] = (max([pending_order["order_id"] for pending_order in self.get_pending()]) + 1)\
			if len(self.get_pending()) else 0
		order["parent_entity"] = self.name
		self.pending.append(order)
		print("ADDING ORDER WITH TIME:", str(order["time"]))
		return order["order_id"]

	def get_order(self, order_id: int):
		if type(order_id) != int:
			raise TypeError("order_id must be integer")

		for order in self.get_pending():
			print("testing order ", order["order_id"])
			if order["order_id"] == order_id:
				print("found match")
				return order
			print("...not match")

	def clear_order(self, order_id):
		pending = self.get_pending()
		valid = list(filter(lambda o: o["order_id"] != order_id, pending))
		# print(valid)
		self.pending = valid


# units are hours ! !!
def motion(entity: Entity, delta: float):
	v = entity.v
	a = entity.a
	dr = v * delta + (1 / 2.0) * a * (delta ** 2.0)
	dv = a * delta
	return [dr, dv]


def sort_orders(orders):
	orders.sort(key=lambda o: o["time"])
	return orders


def motion_seconds(entity: Entity, delta: float or int):
	return motion(entity, delta / 3600.0)


class Game:
	def __init__(self, name: str, game_path: str, load=True, force_new = False):
		self.name = name
		self.system_path = game_path
		self.system_filename = f"system.{self.name}.json"
		self.full_path = os.path.join(self.system_path, self.system_filename)
		if not force_new and not os.path.exists(self.full_path):
			raise Exception("new game being created in illegal context")
		self.system = {"game":
						{"name": self.name,
						"created_on": datetime.datetime.now(),
						"last_modified": datetime.datetime.now(),
						"system_time": datetime.datetime.now()
						},
						"entities": dict[str, Entity](),
						"event_log": []
					}
		# self.system_time = datetime.datetime.now()
		# constants:
		self.LIGHTSPEED = 1079251200  # km/hr
		self.AU_TO_KM = 1.495979e8  # 1 AU = that many kilometers

		# parameters:
		self.ENCOUNTER_RADIUS = 1.6e7  # kilometers
		self.CAPTURE_RADIUS = 1.6e7  # kilometers
		self.DEFENSE_RADIUS = 1.12e7  # kilometers
		self.MAX_INSTANT_ACC = 1.6e7  # km/hr/hr
		self.MAX_INSTANT_VEL = self.LIGHTSPEED
		self.SIM_TICK = datetime.timedelta(seconds=30)  # in seconds.

		if self.save_exists() and load:
			self.load()

	def save_exists(self):
		# check if save file exists already. note this does not verify the contents of the save.
		return (os.path.exists(self.system_path) and os.path.exists(
			os.path.join(self.system_path, self.system_filename)))

	def get_system_time(self):
		return self.system["game"]["system_time"]

	def set_system_time(self, new_time: datetime.datetime):
		self.system["game"]["system_time"] = new_time

	def add_system_time(self, value: datetime.timedelta):
		self.set_system_time(self.get_system_time() + value)

	def new(self, overwrite=False):
		#raise Exception("creating new savefile")
		# create files on disk representing system, if they don't exist.
		start = datetime.datetime.now()
		if self.save_exists() and not overwrite:  # if there's a save file, and we aren't supposed to touch it:
			return
		elif overwrite:  # overwriting. doesn't matter if file already exists.
			system_file = open(self.full_path, "w")
			fresh_json = {
				"game": {"name": self.name, "created_on": start.isoformat(), "last_modified": start.isoformat(),
						"system_time": datetime.datetime.now().isoformat()}, "entities": [], "event_log": []}
			json.dump(fresh_json, system_file)
			system_file.close()

	def load(self):
		system_file = open(os.path.join(self.system_path, self.system_filename), "r")
		loaded_system = json.load(system_file)

		# convert time strings to datetimes:
		loaded_system["game"]["created_on"] = datetime.datetime.fromisoformat(loaded_system["game"]["created_on"])
		loaded_system["game"]["last_modified"] = datetime.datetime.fromisoformat(loaded_system["game"]["last_modified"])
		loaded_system["game"]["system_time"] = datetime.datetime.fromisoformat(loaded_system["game"]["system_time"])

		sys_entities = dict()
		for json_entity in loaded_system["entities"]:
			# convert order time strings to datetime objects
			for order in json_entity["pending"]:
				order["time"] = datetime.datetime.fromisoformat(order["time"])

			entity = Entity(
				name=json_entity["name"],
				captain=json_entity["captain"],
				r=json_entity["r"],
				v=json_entity["v"],
				a=json_entity["a"],
				entity_type=json_entity["type"],
				pending=json_entity["pending"],
				team=json_entity["team"],
				created_on=json_entity["created_on"]
			)

			try:
				entity.authcode = json_entity["authcode"]
			except KeyError:
				pass

			try:
				entity.captured = json_entity["captured"]
			except KeyError:
				pass

			sys_entities[json_entity["name"]] = entity

		loaded_system["entities"] = sys_entities

		self.system = loaded_system

		# print("SYSTEM TIME:",str(self.system["game"]["system_time"]))
		system_file.close()

	def save(self):
		system_file = open(self.full_path, "w")
		"""
		#convert system datetime to time string
		self.system["game"]["system_time"] = self.system["game"]["system_time"].isoformat()
		#convert np arrays representing entity vectors to lists
		for entity in self.system["entities"]:
			entity["r"] = entity["r"].tolist()
			entity["v"] = entity["v"].tolist()
			entity["a"] = entity["a"].tolist()
		#convert order and event dates to strings
		for order in self.get_pending():
			order["time"] = order["time"].isoformat()

		self.system["game"]["last_modified"] = datetime.datetime.now().isoformat()
		json.dump(self.system, system_file, indent=4)
		"""
		print(self.system_as_json())
		json.dump(self.system_as_json(), system_file, indent=4)
		system_file.close()

	def system_as_json(self):
		return {"game":
					{"name": self.system["game"]["name"],
					"created_on": self.system["game"]["created_on"].isoformat(),
					"last_modified": self.system["game"]["last_modified"].isoformat(),
					"system_time": self.get_system_time().isoformat()
					},
					"entities": [entity.as_json() for entity in self.system["entities"].values()],
					"event_log": self.system["event_log"]
				}

	def add_entity(self, name, captain_name, r, v, a, entity_type, pending, team, new_authcode=False):
		if self.get_entity(name):
			return False

		entity = Entity(
			name=name,
			captain=captain_name,
			r=r,
			v=v,
			a=a,
			entity_type=entity_type,
			pending=pending,
			team=team,
			created_on=datetime.datetime.now(),
			authcode=str(uuid.uuid4()) if new_authcode else None
		)

		self.system["entities"][name] = entity
		# print(json.dumps(self.system, indent=4))
		return True  # success

	def get_entity(self, entity_name: str):
		try:
			vessel = self.system["entities"][entity_name]
		except KeyError:
			return None

		return vessel

	def get_authorized_entity(self, entity_name, authcode):
		entity = self.get_entity(entity_name)

		if entity is None:
			raise LookupError(f"No vessel named {entity_name}.")

		if entity.authcode is None:
			raise ValueError(f"Entity {entity_name} has no authcode.")

		if authcode != entity.authcode:
			raise PermissionError(f"Not authorized. {authcode} is not this vessel's authcode.")

		return entity

	def edit_entity(self, entity_name, attribute, value):
		entity = self.get_entity(entity_name)
		entity.__setattr__(attribute, value)

	def get_pending(self, entity_name=None):
		if entity_name:
			return self.get_entity(entity_name).get_pending()
		else:
			pending = []
			for entity in self.system["entities"].values():
				pending += entity.get_pending()
			return pending

	def clear_pending(self, entity_name):
		self.edit_entity(entity_name, "pending", [])

	def get_orders_by_time(self, start, end):
		orders = []
		for order in self.get_pending():
			if (order["time"] >= start) and (order["time"] <= end):
				orders.append(order)
		print("UNSORTED ORDER TIMES:", [str(order["time"]) for order in orders])
		return orders

	def update_interval(self, interval: datetime.timedelta):
		# update interval of constant acceleration
		# interval should be in seconds
		this_moment = self.get_system_time()

		print("\nSTARTING NEW UPDATE SEGMENT FROM",
			str(this_moment),
			"TO", str(this_moment + interval),
			(" (interval of " + str(interval) + ")")
			)

		time = datetime.timedelta(seconds=0)  # elapsed time in seconds
		collisions = []
		instant = self.SIM_TICK  # time per tick in seconds
		while time < interval:
			for entity in self.system["entities"].values():
				step = motion_seconds(entity, instant.total_seconds())
				entity.r = entity.r + step[0]  # update each r by one instant
				entity.v = entity.v + step[1]  # update each v by one instant

				if mag(entity.v) > self.MAX_INSTANT_VEL:  # limit entities to lightspeed
					entity.v = (entity.v / mag(entity.v)) * self.MAX_INSTANT_VEL
			# print("TEST1 velocity:", self.get_entity("TEST1")["v"])
			unfiltered_collisions = self.test_collisions()  # get "colliding" entities
			new_collisions = filter(lambda c: not c in collisions, unfiltered_collisions)
			# filter collisions so objects remaining in radius after one timestep don't
			# keep generating collisions and events:
			"""for collision in unfiltered_collisions:
				if not (collision in collisions):
					new_collisions.append(collision)"""
			collisions = new_collisions
			# find collisions that create events
			for collision in collisions:
				entity_a, entity_b, collision_type = collision
				if entity_a.entity_type == "craft":
					# capture check:
					if collision_type == 'CAPTURE':
						event = {"type": "capture", "args": {"attacker": entity_a.name, "planet": entity_b.name, "kinematics":{"r":entity_a.r.tolist(), "v":entity_a.v.tolist(), "a":entity_a.a.tolist()}},
								"time": (this_moment + time).isoformat()}
						self.add_event(event)
						entity_b.captured = True
						print(event["args"]["attacker"], "captured planet", event["args"]["planet"], "at",
							str(event["time"]))
					# defense check:
					elif collision_type == 'DEFENSE':
						event = {"type": "defense", "args":
							{"defender": entity_a.name, "victim": entity_b.name, "defender_kinematics":{"r":entity_a.r.tolist(), "v":entity_a.v.tolist(), "a":entity_a.a.tolist()}, "victim_kinematics":{"r":entity_b.r.tolist(), "v":entity_b.v.tolist(), "a":entity_b.a.tolist()}},
								"time": (this_moment + time).isoformat()}
						self.add_event(event)
						self.system["entities"].__delitem__(entity_b.name)
						print(event["args"]["defender"], "destroyed vessel", event["args"]["victim"], "at",
							str(event["time"]))
			time += instant

		self.add_system_time(time)
		print("ENDING SEGMENT AT SYSTEM TIME", str(self.get_system_time()))

	def update(self, interval: datetime.timedelta):
		# update over period of time (interval, in hours), including orders and changes in acceleration.
		# collect orders in interval, and sort
		real_start = datetime.datetime.now()
		start_time = self.get_system_time()
		end_time = start_time + interval
		orders = sort_orders(self.get_orders_by_time(start_time, end_time))
		# print("SORTED ORDER TIMES:", [str(order["time"]) for order in orders])
		# self.update_interval for each interval
		for order in orders:
			self.update_interval(order["time"] - start_time)
			entity = self.get_entity(order["parent_entity"])
			if order["task"] == "burn":
				a = np.array(order["args"]["a"])
				#print(f"HANDLING ACCELERATION {a} of type {type(a)}")
				a = ((a / mag(a)) * self.MAX_INSTANT_ACC) if (
						mag(a) > self.MAX_INSTANT_ACC) else a  # limit acceleration to max
				entity.a = a
				self.add_event({'type': "burn",
								"args": {
									"vessel": entity.name,
									"a": order["args"]["a"],
									"kinematics":{"r":entity.r.tolist(), "v":entity.v.tolist(), "a":entity.a.tolist()}
								},
								"time": order["time"].isoformat()
								})
		# print("vessel", order["parent_entity"], "set new burn", order["args"], "at", str(order["time"]))
		# update remaining subinterval between last order and end of whole interval
		remaining_timedelta = end_time - self.get_system_time()
		print("SEGMENTS DONE, REMAINING TIME", remaining_timedelta)
		self.update_interval(remaining_timedelta)
		print("FINISHED OVERALL UPDATE AT SYSTEM TIME", self.get_system_time())
		print(f"simulation complete in {datetime.datetime.now() - real_start}")
		# remove processed orders
		for order in orders:
			self.get_entity(order["parent_entity"]).clear_order(order["order_id"])
		return

	def update_to(self, end_date: datetime.datetime):
		# end_date: datetime
		now = self.get_system_time()
		interval = abs(end_date - now)
		if interval < datetime.timedelta(0):
			raise ValueError(f"Simulation attempting to time travel by {interval} seconds.")
		print("updating to", end_date, "with interval of", interval, "seconds")
		self.update(interval)

	def test_collisions(self):
		collisions = set()
		entities = set(self.system["entities"].values())
		for entity_a in filter(lambda e: e.entity_type != "planet", entities):
			for entity_b in filter(lambda e: e.name != entity_a.name, entities):
				# capture check:
				if (entity_a.team == team.ATTACKER and
						entity_b.entity_type == "planet" and
						entity_b.captured is False and
						(dist(entity_a.r, entity_b.r) <= self.CAPTURE_RADIUS)):
					collisions.add((entity_a, entity_b, 'CAPTURE'))
				# defense check:
				if (entity_a.team == team.DEFENDER and
						entity_b.team == 1 and
						dist(entity_a.r, entity_b.r) <= self.DEFENSE_RADIUS):
					collisions.add((entity_a, entity_b, 'DEFENSE'))

		return collisions

	def add_event(self, event):
		# event = {"type":burn|defense|capture, "args":{keys to entities or coords}, "time":ISO time string}
		if self.system["event_log"]:
			# event id is previous event id + 1
			event["event_id"] = self.system["event_log"][-1]["event_id"] + 1
		else:
			event["event_id"] = 0
		self.system["event_log"].append(event)

	def get_event_log(self, start: datetime.datetime, end: datetime.datetime):
		start = start if start else datetime.datetime.fromtimestamp(0)  # the epoch
		end = end if end else self.get_system_time()

		if start:
			events = []
			for event in self.system["event_log"]:
				if (datetime.datetime.fromisoformat(event["time"]) >= start) and (
						datetime.datetime.fromisoformat(event["time"]) <= end):
					events.append(event)
		else:
			events = self.system["event_log"]

		return events
