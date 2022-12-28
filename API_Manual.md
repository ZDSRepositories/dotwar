# Dotwar API Manual
This manual details the endpoints of a dotwar/myrmidon server (version myr1 specifically.)

For each endpoint it lists the purpose, URI, required parameters, optional parameters, and example output.

## Overview
All endpoints are given as partial URLs to be appended to the web address of a dotwar server.

For example, endpoint "/games" on server dotwar.pythonanywhere.com would be called by sending a request "dotwar.pythonanywhere.com/games".

All endpoints expect POST requests and will error if a different method is used.

All key-value pairs that are parameters for an endpoint are to be provided as POST headers.

Some endpoints will trigger an update run of a simulation. Some of these will update the simulation before the endpoint does its job (most info-related endpoints such as /scan) while some will update the simulation after the endpoint does its job (e.g. /add_order).

## Parameters and Formatting
All parameters are provided as POST headers, although this page lists them as GET query strings for convenience.\
All dates are expected and returned as ISO-format strings, specifically those compatible with Python's `datetime` module.\
Other parameters are expected to be strings, or strings of valid JSON (that is, parseable by Python `json.loads()`.)

Several endpoints have parameters in common:
param name | expected format | effect
---|---|---
`html` | Boolean | Determine if JSON or pretty HTML will be returned
`filter` | JSON object | Only return entries in list whose key-value pairs match those in `filter`
`authcode` | UUID4 string | Unique vessel authcode required for vessel operations



## Endpoints

### /
Provides HTML page with the server's welcome message and list of games.

### /games

Provides a list of simulations that exist on the server.

Required parameters: none.

Optional parameters: none.

Output: a json object with a `games` key containing a list of names.

Updates sim: no.

#### Example:

Call: `/games`

Output: 

    {
    "ok": true,
    "games": ["TESTGAME"]
    }

### /game/[name]/status
Provides status and current simulation time of the game of specified name.

Required parameters: none.

Optional parameters: `html`

Updates sim: before operation.

#### Examples: 

Call: `/game/TESTGAME/status` with `html=0`

Output: 

    {
    "ok": true,
    "game": 
        {"name": "TESTGAME", 
        "created_on": "2022-12-16T11:24:18.194421", 
        "last_modified": "2022-12-16T11:24:18.194421", 
        "system_time": "2022-12-22T17:41:55.194421"
        }
    }

Call: `/game/TESTGAME/status` with `html=1`

Output: 
```
Game 'TESTGAME' status:
Created on: 2022-12-16T11:24:18.194421 (Dec 16 2022, 11:24:18)
System time: 2022-12-22T17:41:55.194421 (Dec 22 2022, 17:41:55)
```

### /game/[name]/scan
Lists the position, heading, acceleration, and other public properties of each object in the system.

Required parameters: none.

Optional parameters: `html` `filter`

Updates sim: before operation.

#### Examples:

Call: `/game/TESTGAME/scan`

Output: 
    
    {"ok": true,
    "entities": [
        {"name": "TEST1", 
        "captain": "ADMIN", 
        "r": [923492884.5, 0.0, 0.0], 
        "v": [42963.000000000015, 0.0, 0.0], 
        "a": [1, 0, 0], 
        "type": "craft", 
        "team": 0, 
        "created_on": "2022-12-27T18:42:58.073688"}
     ]}
 
 Call: `/game/TESTGAME/scan` with `html=1`
 
 Output:
 
 ![image](https://user-images.githubusercontent.com/89665494/209775961-4d97f043-ef56-4eab-a6f0-587ceefb0f64.png)

### /game/[name]/summary

List events from game start or specified range.
Alias `/game/[name]/event_log`.

Required parameters: none.

Optional parameters: `html` `start` `end`

Updates sim: before operation.

#### Examples

Call: `/game/TESTGAME/summary`

Output:
```
{"ok": true, 
"events": [
    {"type": "defense", "args": {"defender": "TEST1", "victim": "TEST2"}, "time": "2022-12-27T18:42:58.068610", "event_id": 0}, 
    {"type": "capture", "args": {"attacker": "TEST2", "planet": "Earth"}, "time": "2022-12-27T18:42:58.068610", "event_id": 1}, 
    {"type": "burn", "args": {"vessel": "TEST1", "a": [1, 0, 0], "position": [647999.9999999906, 0.0, 0.0]}, "time": "2022-12-27T19:42:58.068610", "event_id": 2}
]}
```

Call: `game/TESTGAME/summary` with `html=1` and `start=1969-12-31T18:00:00`\
Output:
```
Events between 1969-12-31T18:00:00 and current time:
Dec 27 2022, 18:42:58  [DEF] vessel TEST1 destroyed vessel TEST2
Dec 27 2022, 18:42:58  [ATK] vessel TEST2 captured Earth
Dec 27 2022, 19:42:58  [NAV] vessel TEST1 started burn [1, 0, 0] while at coords [648000.0, 0.0, 0.0]
```

### /game/[name]/agenda
Display the pending orders of a vessel.

Required parameters: `vessel` `authcode`

Optional parameters: `html`

Updates sim: before operation.

#### Examples

Call: `/game/TESTGAME/agenda` with `vessel=TEST1` and `authcode=733a9f3f-debc-42a0-8c71-7da1a7debdca`\
Output: 
```
{"ok": true, 
"agenda": [
    {'task': 'burn', 
    'args': {'a': [1, 0, 0]}, 
    'time': '2022-12-28T02:52:59.123854', 
    'order_id': 0, 
    'parent_entity': 'TEST1'}
]}
```

Call: `/game/TESTGAME/agenda` with `vessel=TEST1` and `authcode=733a9f3f-debc-42a0-8c71-7da1a7debdca` and `html=1`\
Output:
```
Pending orders for vessel TEST1:
at 02:52 AM on Wednesday, Dec 28, 2022: burn [1.000 0.000 0.000] ; order ID: 0
```

### /game/[name]/add_order
Add an order to a vessel's list of pending orders.

Required parameters: `vessel` `authcode` `order`

Optional parameters: `html`

Updates sim: after operation.

#### Examples
Call: `/game/TESTGAME/agenda` with `vessel=TEST1` and `authcode=733a9f3f-debc-42a0-8c71-7da1a7debdca` and `order={"task": "burn", "args": {"a": [0, 0, 0]}, "time": "2022-12-28T19:41:38.176481"}`\
Output: 
```
{
"ok": true, 
"msg": 
    "order {'task': 'burn', 'args': {'a': [0, 0, 0]}, 'time': '2022-12-28T19:41:38.176481'} successfully given to vessel TEST1"
}
```

Call: `/game/TESTGAME/agenda` with `vessel=TEST1` and `authcode=733a9f3f-debc-42a0-8c71-7da1a7debdca` and `order={"task": "burn", "args": {"a": [0, 0, 0]}, "time": "2022-12-28T19:41:38.176481"}` and `html=1`\
Output: `Order 'burn <0.000 0.000 0.000> at 07:41 PM on Wednesday, Dec 28, 2022' successfully given to vessel TEST1.`

