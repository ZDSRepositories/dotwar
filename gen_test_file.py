from dotwar_classes import *

g = Game("TESTGAME", "C:\\Users\\1zada\\PycharmProjects\\dotwar")
g.new(overwrite=True)
g.load()

g.add_entity("TEST1", "ADMIN", [0, 0, 0], [0, 0, 0], [0.0, 0, 0], "craft", [], 0, True)
g.add_entity("TEST2", "ADMIN", [10, 10, 10], [0, 0, 0], [2, 2, 2], "craft", [], 1, True)
g.add_entity("Earth", None, [0, 0, 0], [0, 0, 0], [0, 0, 0], "planet", [], -1)
g.edit_entity("Earth", "captured", False)
# g.save()
# g.load()

"""g.add_order("TEST1", task="burn", time=(g.system["game"]["system_time"] + datetime.timedelta(hours=1)), args={"a":[0.1, 0.0, 0.0]})
g.add_order("TEST1", task="burn", time=(g.system["game"]["system_time"] + datetime.timedelta(hours=3)), args={"a":[0.0, -0.1, 0.0]})
#print("pending orders:",g.get_pending())
#print(g.update(25))
g.update(25/10)"""
test1 = g.get_entity("TEST1")
test1.add_order(task="burn", time=g.system["game"]["system_time"], args={"a":[60.0, 0.0, 0.0]})
# print("pending orders:",g.get_pending())
# print("TEST1 velocity:",g.get_entity("TEST1")["v"])
g.update(datetime.timedelta(seconds=1))
g.save()
# print("event log:")
print("Events:")
[print(" ", event) for event in g.system["event_log"]]
print("Pending orders:")
[print(order) for order in g.get_pending("TEST1")]
print("entities", g.system["entities"])
