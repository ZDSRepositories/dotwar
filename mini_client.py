import datetime

import dotwar_classes

game = dotwar_classes.Game(0, "TESTGAME", "C:\\Users\\1zada\\PycharmProjects\\dotwar")
game.load()
#print(game.system)

print("Available craft:")
[(print(e["name"]) if e["type"]=="craft" else None) for e in game.system["entities"]]

vessel_name = input("Vessel name? ")

def scan(vessel_name, game):
    print("Local scan", str(game.system["game"]["system_time"]), "from", vessel_name)
    print("Found", len(game.system["entities"]) - 1, "entities.")
    header = "NAME\tTYPE\tCAPTAIN\tPOSITION\tHEADING \tACCELERATION"
    print(header)
    #print("-"*len(header.split("\t"))*8)
    for e in game.system["entities"]:
        if e["name"] != vessel_name:
            print(" \t".join([str(attr) for attr in
                              [e["name"],
                               e["type"],
                               e["captain"] if e["captain"] else "----",
                               e["r"],
                               e["v"],
                               e["a"]]]))
    print("Scan complete.")

def summarize(vessel_name, last_seen, game):
    events = game.event_log(last_seen, None)
    print("Listing events since", str(last_seen), end=".\n")
    for event in events:
        desc = ""
        if event["type"] == "capture":
            desc = ["vessel", event["args"][0], "captured", event["args"][1]]
        elif event["type"] == "defense":
            desc = ["vessel", event["args"][0], "destroyed vessel", event["args"][1]]
        elif event["type"] == "burn":
            desc = ["vessel", event["args"][0], "started burn", str(event["args"][1]), "while at coords", str(event["args"][2])]
        print(str(event["time"]),"\t"," ".join(desc))
    print("Summary complete.")
scan(vessel_name, game)
summarize(vessel_name, datetime.datetime.fromisoformat(game.system["game"]["created_on"]), game)