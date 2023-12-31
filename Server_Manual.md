# Running a server

First you need to create a game.

    python3 dotwar.py add_game mygame

This will create the game state file as "system.mygame.json".

Now add a defending ship.

    python3 dotwar.py add_ship mygame 'Defender' Fred 0 0 0 0

This will create a ship named "Defender" owned by user "Fred" at coordinates (0,0,0). The team is 0, meaning that the ship is a defender.

Add an attacking ship.

    python3 dotwar.py add_ship mygame 'Attacker' Bill 1000000 45 -6 1

This will create a ship named "Attacker" owned by user "Bill" at coordinates (1000000,45,-6). The team is 1, meaning that the ship is an attacker.

Create "config.json". In this case we will create a local game. Replace "$DOTWAR" with the path to your Dotwar repository.

    {
	    "server_addr": "localhost",
	    "server_port": 3587,
	    "dir": "$DOTWAR",
	    "game_dir": "$DOTWAR",
	    "static_dir": "$DOTWAR/static",
	    "debug": true,
	    "welcome": "Welcome to my myrmidon/dotwar server!"
    }

The default port is 80, which on Linux will require you run the server as root, so it's best to create a "config.json" to override that.

Now run the server.

    python3 dotwar_server.py

You should now be able to open "http://localhost:3587/" in your browser and view the minimal built-in client.
