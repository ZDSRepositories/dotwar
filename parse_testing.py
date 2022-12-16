import datetime

keywords = {
    "hours":{"-1":int},
    "burn":{"1":int, "2":int, "3":int}
    }

translations = {"hour":"hours"} #aliases
time_keywords = ["seconds", "hours", "minutes", "days"]
verb_keywords = ["burn"]
s = input("input command: ")
tokens = s.split()
#translate tokens to their aliases
for i in range(len(tokens)):
    token = tokens[i]
    if token in translations:
        tokens[i] = translations[token]

# detect meaningful tokens and assemble them into 'phrases'
#a phrase is a token and the set of other tokens relevant to it
def phrasify(tokens, keywords):
    phrases = []
    for i in range(len(tokens)):
        token = tokens[i]
        if token in keywords:
            #start collecting arguments the keyword specifies
            arg_indices = keywords[token]
            args=[]
            for arg_index in arg_indices:
                arg = tokens[i + int(arg_index)]
                try:
                    arg_type = arg_indices[arg_index]
                    arg = arg_type(arg)
                    args.append(arg)
                except ValueError:
                    raise ValueError("keyword "+token+" expected token of type "+str(arg_type)+" at index "+str(i + int(arg_index))+" but found "+arg)
            phrases.append([token, args])
    return phrases

#take phrases and turn them into 'items', replacing input data with python objects as appropriate e.g. timedeltas
#an item is something relevant to the top-level parser:
# it is a 'verb' (command, action) or 'noun' (data) that is directly relevant to a command.
def itemify(phrases, time_keywords, verb_keywords):
    # item types:
    #   INTERVAL, DATE, NAME, TRIPLE, VERB_BURN, VERB_AGENDA, VERB_ADD_ORDER, VERB_SCAN, VERB_SUMMARY
    items = []
    for phrase in phrases:
        if phrase[0] in time_keywords:
            delta = datetime.timedelta(**{phrase[0]:phrase[1][0]})
            items.append(["INTERVAL", delta])
        elif phrase[0] in verb_keywords:
            if phrase[0] == "burn":
                items.append(["VERB_BURN", phrase[1]])
    return items


phrases = phrasify(tokens, keywords)
items = itemify(phrases, time_keywords, verb_keywords)
print(items)
