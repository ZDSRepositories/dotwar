import os
import datetime
import json
import uuid
from typing import Dict, Union, List, Any

import numpy as np


def dist(a, b):
	c = np.array(b) - np.array(a)
	return abs((c.dot(c)) ** (1 / 2))


def mag(a):
	return np.sqrt(a.dot(a))


def datetime_decode_hook(obj):
	try:
		# print("decoding as datetime")
		return datetime.datetime.fromisoformat(obj)
	except:
		return datetime.datetime.fromisoformat(obj)


class Game:

	def __init__(self, name: str, game_path: str, load=True):
		self.name = name
		self.system_path = game_path
		self.system_filename = "system." + self.name + ".json"
		self.full_path = os.path.join(self.system_path, self.system_filename)
		self.system = {"game": {"name": self.name, "created_on": datetime.datetime.now(),
								"last_modified": datetime.datetime.now(),
								"system_time": datetime.datetime.now()}, "entities": [], "event_log": []}
		# self.system_time = datetime.datetime.now()
		self.ENCOUNTER_RADIUS = 1.6e7  # kilometers
		self.MAX_INSTANT_ACC = 1.6e7  # km/hr/hr
		self.LIGHTSPEED = 1079251200  # km/hr
		self.MAX_INSTANT_VEL = self.LIGHTSPEED
		self.SIM_TICK = 1  # in seconds.
		if self.save_exists() and load:
			self.load()

	def save_exists(self):
		# check if save file exists already. note this does not verify the contents of the save.
		return (os.path.exists(self.system_path) and os.path.exists(
			os.path.join(self.system_path, self.system_filename)))

	def system_time(self):
		return self.system["game"]["system_time"]

	def new(self, overwrite=False):
		# create files on disk representing system, if they don't exist.
		start = datetime.datetime.now()
		if self.save_exists() and not overwrite:  # if there's a save file and we aren't supposed to touch it:
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
		self.system = json.load(system_file)
		# convert system time string to datetime:
		self.system["game"]["system_time"] = datetime.datetime.fromisoformat(self.system["game"]["system_time"])
		# convert lists representing entity vectors to np arrays
		for entity in self.system["entities"]:
			entity["r"] = np.array(entity["r"])
			entity["v"] = np.array(entity["v"])
			entity["a"] = np.array(entity["a"])
		# convert order time strings to datetime objects
		for order in self.get_pending():
			order["time"] = datetime.datetime.fromisoformat(order["time"])
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
		json.dump(self.as_json(), system_file, indent=4)
		system_file.close()

	def as_json(self):
		json_compatible = self.system
		# convert system datetime to time string
		json_compatible["game"]["system_time"] = self.system["game"]["system_time"].isoformat() if (
				type(self.system["game"]['system_time']) != str) else self.system["game"]["system_time"]
		# convert np arrays representing entity vectors to lists
		for entity in json_compatible["entities"]:
			try:
				entity["r"] = entity["r"].tolist()
				entity["v"] = entity["v"].tolist()
				entity["a"] = entity["a"].tolist()
			except:
				pass
			for order in entity["pending"]:
				try:
					order["time"] = order["time"].isoformat()
				except:
					pass
		return json_compatible

	def add_entity(self, name, captain_name, r, v, a, entity_type, pending, team, new_authcode=False):
		if name in [entity["name"] for entity in self.system["entities"]]:
			return False
		entity = {"name": name, "captain": captain_name, "r": np.array(r), "v": np.array(v), "a": np.array(a),
				  "type": entity_type,
				  "pending": pending, "team": team, "created_on": datetime.datetime.now().isoformat()}
		if new_authcode: entity["authcode"] = str(uuid.uuid4())
		self.system["entities"].append(entity)
		# print(json.dumps(self.system, indent=4))
		return True  # success

	def get_entity(self, entity_name):
		for entity in self.system["entities"]:
			if entity["name"] == entity_name:
				return entity

	def edit_entity(self, entity_name, attribute, value):
		entity = self.get_entity(entity_name)
		entity[attribute] = value

	def add_order(self, entity_name, task, args, time):
		# order example: {"task":"burn", args:{"a":[0, 20, 1]}, "time":datetime}
		entity = self.get_entity(entity_name)
		order = {
			"task": task,
			"args": args,
			"time": datetime.datetime.fromisoformat(time) if type(time) == str else time}
		if task == "burn":
			if "a" not in args:
				raise Exception("Burn order creation missing 'a' in args")

		order["order_id"] = (max([pending_order["order_id"] for pending_order in entity["pending"]]) + 1) if entity[
			"pending"] else 0
		order["parent_entity"] = entity_name
		entity["pending"].append(order)
		print("ADDING ORDER WITH TIME:", str(order["time"]))
		return order["order_id"]

	def get_pending(self, entity_name=None):
		if entity_name:
			return self.get_entity(entity_name)["pending"]
		else:
			pending = []
			for entity in self.system["entities"]:
				pending += entity["pending"]
			return pending

	def clear_pending(self, entity_name):
		self.edit_entity(entity_name, "pending", [])

	def get_order(self, entity_name, order_id):
		for order in self.get_entity(entity_name)["pending"]:
			if order["order_id"] == order_id:
				return order

	def get_orders_by_time(self, start, end):
		orders = []
		for order in self.get_pending():
			if (order["time"] >= start) and (order["time"] <= end):
				orders.append(order)
		print("UNSORTED ORDER TIMES:", [str(order["time"]) for order in orders])
		return orders

	def clear_order(self, entity_name, order_id):
		self.get_entity(entity_name)["pending"].remove(self.get_order(entity_name, order_id))

	def sort_orders(self, orders):
		orders.sort(key=lambda o: o["time"])
		return orders

	def motion(self, entity_name, dt):
		entity = self.get_entity(entity_name)
		v = np.array(entity["v"])
		a = np.array(entity["a"])
		dr = v * dt + (1 / 2.0) * a * (dt ** 2.0)
		dv = a * dt
		return [dr, dv]

	def update_interval(self, interval):
		# update interval of constant acceleration
		# interval should be in hours
		print("\nSTARTING NEW UPDATE SEGMENT FROM",
			  str(self.system["game"]["system_time"]),
			  "TO", str(self.system["game"]["system_time"] + datetime.timedelta(hours=interval)),
			  (" (interval of " + str(datetime.timedelta(hours=interval)) + ")")
			  )
		time = 0  # elapsed time in seconds
		collisions = []
		instant = self.SIM_TICK  # time per tick in seconds
		while (time / 3600) < interval:
			for entity in self.system["entities"]:
				step = self.motion(entity["name"], instant / 3600)
				entity["r"] = entity["r"] + step[0]  # update each r by one instant
				entity["v"] = entity["v"] + step[1]  # update each v by one instant

				if mag(entity["v"]) > self.MAX_INSTANT_VEL:  # limit entities to lightspeed
					entity["v"] = (entity["v"] / mag(entity["v"])) * self.MAX_INSTANT_VEL
			# print("TEST1 velocity:", self.get_entity("TEST1")["v"])
			unfiltered_collisions = self.test_collisions(self.ENCOUNTER_RADIUS)  # get "colliding" entities
			new_collisions = []
			# filter collisions so objects remaining in radius after one timestep don't
			# keep generating collisions and events:
			for collision in unfiltered_collisions:
				if not (collision in collisions):
					new_collisions.append(collision)
			collisions = new_collisions
			# find collisions that create events
			for collision in collisions:
				entity_a, entity_b = collision
				if entity_a["type"] == "craft":
					if entity_a["team"] == 1 and entity_b["type"] == "planet" and entity_b["captured"] is False:
						event = {"type": "capture", "args": {"attacker": entity_a["name"], "planet": entity_b["name"]},
								 "time": self.system["game"]["system_time"].isoformat()}
						self.add_event(event)
						entity_b["captured"] = True
						print(event["args"]["attacker"], "captured planet", event["args"]["planet"], "at",
							  str(event["time"]))
					elif entity_a["team"] == 0 and entity_b["team"] == 1:
						event = {"type": "defense", "args": {"defender": entity_a["name"], "victim": entity_b["name"]},
								 "time": self.system["game"]["system_time"].isoformat()}
						self.add_event(event)
						self.system["entities"].remove(entity_b)
						print(event["args"]["defender"], "destroyed vessel", event["args"]["victim"], "at",
							  str(event["time"]))
			time += instant

		self.system["game"]["system_time"] += datetime.timedelta(seconds=time)
		print("ENDING SEGMENT AT SYSTEM TIME", str(self.system_time()))

	def update(self, interval):
		# update over period of time (interval, in hours), including orders and changes in acceleration.
		# collect orders in interval, and sort
		end_time = self.system["game"]["system_time"] + datetime.timedelta(hours=interval)
		orders = self.get_orders_by_time(self.system["game"]["system_time"],
										 self.system["game"]["system_time"] + datetime.timedelta(hours=interval))
		orders = self.sort_orders(orders)
		# print("SORTED ORDER TIMES:", [str(order["time"]) for order in orders])
		# self.update_interval for each interval
		for order in orders:
			self.update_interval(((order["time"] - self.system["game"]["system_time"]).total_seconds()) / 3600.0)
			if order["task"] == "burn":
				a = np.array(order["args"]["a"])
				a = ((a / mag(a)) * self.MAX_INSTANT_ACC) if (
						mag(a) > self.MAX_INSTANT_ACC) else a  # limit acceleration to max
				position = self.get_entity(order["parent_entity"])["r"].tolist()
				self.edit_entity(order["parent_entity"], "a", a)
				self.add_event({'type': "burn", "args": {"vessel": order["parent_entity"], "a": order["args"]["a"],
														 "position": position}, "time": order["time"].isoformat()})
		# print("vessel", order["parent_entity"], "set new burn", order["args"], "at", str(order["time"]))
		# update remaining subinterval between last order and end of whole interval
		remaining_timedelta = end_time - self.system["game"]["system_time"]
		print("SEGMENTS DONE, REMAINING TIME", remaining_timedelta)
		self.update_interval(remaining_timedelta.total_seconds() / 3600.0)
		print("FINISHED OVERALL UPDATE AT SYSTEM TIME", self.system_time())
		# remove processed orders
		for order in orders:
			self.clear_order(order["parent_entity"], order["order_id"])
		return

	def update_to(self, end_date):
		# end_date: datetime
		now = self.system["game"]["system_time"]
		interval = ((end_date - now).total_seconds()) / 3600
		print("updating to", end_date, "with interval of", interval, "hours")
		self.update(interval)

	def test_collisions(self, radius):
		collisions = []
		for entity_a in self.system["entities"]:
			for entity_b in self.system["entities"]:
				if not (entity_a["name"] == entity_b["name"]):
					if dist(entity_a["r"], entity_b["r"]) <= self.ENCOUNTER_RADIUS:
						collisions.append([entity_a, entity_b])

		return collisions

	def add_event(self, event):
		# event = {"type":burn|defense|capture, "args":{keys to entities or coords}, "time":ISO time string}
		if self.system["event_log"]:
			# event id is previous event id + 1
			event["event_id"] = self.system["event_log"][-1]["event_id"] + 1
		else:
			event["event_id"] = 0
		self.system["event_log"].append(event)

	def event_log(self, start: datetime.datetime, end: datetime.datetime):
		end = end if end else self.system["game"]["system_time"]
		start = start if start else datetime.datetime.fromtimestamp(0)  # the epoch

		if start:
			events = []
			for event in self.system["event_log"]:
				if (datetime.datetime.fromisoformat(event["time"]) >= start) and (
						datetime.datetime.fromisoformat(event["time"]) <= end):
					events.append(event)
		else:
			events = self.system["event_log"]

		return events
