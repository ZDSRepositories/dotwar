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

Several endpoints have optional parameters in common:
param name | expected format | effect
---|---|---
`html` | Boolean | Determine if JSON or pretty HTML will be returned
`filters` | JSON object | Only return entries in list whose key-value pairs match those in `filters`
`authcode` | UUID4 string | Unique vessel authcode required for vessel operations



## Endpoints

### /
Provides HTML page with the server's welcome message and list of games.

### /games

Provides a list of simulations that exist on the server.

Required parameters: none.

Optional parameters: none.

Output: a json object with a `games` key containing a list of names.

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
