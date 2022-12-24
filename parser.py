import datetime


class Parser:
    # noinspection PyDefaultArgument
    def __init__(self,
                keywords={
                    "hours": {-1: int},
                    "seconds": {-1: int},
                    "minutes": {-1: int},
                    "days": {-1: int},

                    "burn": {1: int, 2: int, 3: int},
                    "agenda": {},
                    "scan": {}
                },
                translations={"hour": "hours"},
                time_keywords = ["seconds", "hours", "minutes", "days"],
                verb_keywords=["burn", "scan", "agenda"],

                ):
        self.keywords = keywords
        self.translations = translations
        self.time_keywords = time_keywords
        self.verb_keywords= verb_keywords

    def tokenify(self, s):
        tokens = s.split()  # example: "in 2 hours burn 0 0 0"
        # translate tokens to their aliases
        for i in range(len(tokens)):
            token = tokens[i]
            if token in self.translations:
                tokens[i] = self.translations[token]
        return tokens

    # detect meaningful tokens and assemble them into 'phrases'
    # a phrase is a token and the set of other tokens relevant to it
    def phrasify(self, s=None, tokens=None):
        if tokens == None:
            tokens = self.tokenify(s)
        phrases = []
        for i in range(len(tokens)):
            token = tokens[i]
            if token in self.keywords:
                # print("found keyword:", token)
                # start collecting arguments the keyword specifies
                arg_indices = self.keywords[token]
                args = []
                for arg_index in arg_indices:
                    arg = tokens[i + int(arg_index)]
                    try:
                        arg_type = arg_indices[arg_index]
                        arg = arg_type(arg)
                        args.append(arg)
                    except ValueError:
                        raise ValueError(
                            "keyword " + token + " expected token of type " + str(arg_type) + " at index " + str(
                                i + int(arg_index)) + " but found '" + arg +"'")
                phrases.append([token, args])
        return phrases

    # take phrases and turn them into 'items', replacing input data with python objects as appropriate e.g. timedeltas
    # an item is something relevant to the top-level parser:
    # it is a 'verb' (command, action) or 'noun' (data) that is directly relevant to a command.
    def itemify(self, s=None, phrases=None):
        if phrases == None:
            phrases = self.phrasify(s=s)
        item_types = ["INTERVAL", "DATE", "NAME", "VERB_BURN", "VERB_AGENDA", "VERB_SCAN", "VERB_SUMMARY"]
        items = []
        for phrase in phrases:
            if phrase[0] in self.time_keywords:
                # print("found time phrase:", phrase[0])
                delta = datetime.timedelta(**{phrase[0]: phrase[1][0]})
                items.append(["INTERVAL", delta])
            elif phrase[0] in self.verb_keywords:
                # print("found verb phrase:", phrase[0])
                items.append(["VERB_"+phrase[0].upper(), *phrase[1:]])
            break
        return items

    def classify(self, s=None, items=None):
        if items == None:
            items = self.itemify(s=s)



p = Parser()
s = input("command vessel> ")
print(p.itemify(s=s))