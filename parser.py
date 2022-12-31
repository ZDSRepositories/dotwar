import datetime


class Parser:
	# noinspection PyDefaultArgument
	def __init__(self,
	             keywords={
		             "hours": {-1: float},
		             "seconds": {-1: float},
		             "minutes": {-1: float},
		             "days": {-1: float},

		             "at":{1:str, 2:str},

		             "burn": {1: float, 2: float, 3: float},
		             "agenda": {},
		             "scan": {}
	             },
	             translations={"hour": "hours"},
	             time_keywords=["seconds", "hours", "minutes", "days"],
	             verb_keywords=["burn", "scan", "agenda"],
	             command_signatures=[{"verb":"VERB_BURN", "required_items":[["INTERVAL", "DATE"]], "required_context":["authcode"]}]
	             ):
		self.keywords = keywords
		self.translations = translations
		self.time_keywords = time_keywords
		self.verb_keywords = verb_keywords
		self.command_signatures = command_signatures

	def tokenify(self, input_string):
		tokens = input_string.split()  # example: "in 2 hours burn 0 0 0"
		# translate tokens to their aliases
		for i in range(len(tokens)):
			token = tokens[i]
			if token in self.translations:
				tokens[i] = self.translations[token]
		return tokens

	# detect meaningful tokens and assemble them into 'phrases'
	# a phrase is a token and the set of other tokens relevant to it
	def phrasify(self, input_string=None, tokens=None):
		if tokens is None:
			tokens = self.tokenify(input_string)
		phrases = []
		for i in range(len(tokens)):
			token = tokens[i]
			if token in self.keywords:
				# print("found keyword:", token)
				# start collecting arguments the keyword specifies
				arg_indices = self.keywords[token] #expected locations of arguments
				args = [] # collected arguments
				for arg_index in arg_indices: #for each expected position
					arg = tokens[i + int(arg_index)] #collect arg
					arg_type = arg_indices[arg_index]  # expected type of arg
					try:
						arg = arg_type(arg) # convert collected arg string to expected type
						args.append(arg) # add converted arg to args
					except ValueError:
						raise ValueError(
							"keyword " + token + " expected token of type " + str(arg_type) + " at index " + str(
								i + int(arg_index)) + " but found '" + arg + "'")
				phrases.append([token, args])
		return phrases

	# take phrases and turn them into 'items', replacing input data with python objects as appropriate e.g. timedeltas
	# an item is something relevant to the top-level parser:
	# it is a 'verb' (command, action) or 'noun' (data) that is directly relevant to a command.
	def itemify(self, input_string=None, phrases=None):
		if phrases is None:
			phrases = self.phrasify(input_string=input_string)
		item_types = ["INTERVAL", "DATE", "NAME", "VERB_BURN", "VERB_AGENDA", "VERB_SCAN", "VERB_SUMMARY"]
		items = []
		for phrase in phrases:
			print("testing phrase", phrase)
			if phrase[0] in self.time_keywords:
				print("found time phrase:", phrase[0])
				delta = datetime.timedelta(**{phrase[0]: phrase[1][0]})
				items.append(["INTERVAL", delta])
			elif phrase[0] in self.verb_keywords:
				# print("found verb phrase:", phrase[0])
				items.append(["VERB_" + phrase[0].upper(), *phrase[1:]])
			elif phrase[0] == "at":
				items.append(
					["DATE",
					 datetime.datetime.strptime(" ".join(phrase[1]), "%Y-%m-%d %H:%M")]
				)
		return items

	# take list of items and determine what command it matches,
	# classifying it based on verb.
	# return a representation of the command: a verb and relevant items
	# i.e {"verb":"burn", "interval":timedelta, "a":[0,0,0], "missing_headers":["authcode", "time"]}
	# or  {"verb":"burn", "time":datetime, "a":[0,0,0], "missing_headers":["authcode"]}
	def classify(self, input_string=None, items=None):
		if items is None:
			items = self.itemify(input_string=input_string)
		verb = None
		signature = None
		item_labels = [item[0] for item in items]
		item_contents = [item[1] for item in items]
		for signature_candidate in self.command_signatures:
			if signature_candidate["verb"] in item_labels:
				signature = signature_candidate
				break
		verb = signature["verb"]

		for required_item in signature["required_items"]:
			print("searching in", [e[0] for e in filter(lambda i: (i[0]==required_item or i[0] in required_item), items)])
			if not [e[0] for e in filter(lambda i: (i[0]==required_item or i[0] in required_item), items)]:
				raise Exception(f"signature for {verb} expected {required_item}")

		if verb == "VERB_BURN":
			if "DATE" in item_labels:
				time = None
				item = list(filter(lambda i: i[0]=="TIME", items))[0]
				return {"endpoint":"/add_order",
				        "headers":{"time":time.isoformat()},
				        "incomplete_headers":["vessel", "authcode"]
				        }
			elif "INTERVAL" in item_labels:
				return {"endpoint": "/add_order",
				        "headers": {},
				        "incomplete_headers": ["vessel", "authcode", "time"],
				        "context":{}
				        }




parser_global = Parser()
input_string_global = input("command vessel> ")
print("tokens:", parser_global.tokenify(input_string=input_string_global))
print("phrases:", parser_global.phrasify(input_string=input_string_global))
print("items:", parser_global.itemify(input_string=input_string_global))
print("result:", parser_global.classify(input_string=input_string_global))
