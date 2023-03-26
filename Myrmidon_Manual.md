# Dotwar/Myrmidon Manual
Welcome to Dotwar. You are a dot, somewhere in the vicinity of dot Earth.\
Specifically, your spacecraft is a dot, traversing 3d space in your stead.\
If you are an attacker, your mission is to capture Earth.\
If you are a defender, your mission is to eliminate all attackers.

## Gameplay

### Capture, Elimination, and Winning
The attackers' goal is to capture Earth. Earth is instantly captured if any attacker is within 1.6e7 km of it.\
The defenders' goal is to eliminate all attackers. An attacker is instantly destroyed if a defender gets within 1.12e7 km of it (70% of the capture radius.)\
If all attackers are eliminated, the defenders win.\
These numbers are slightly modified from the myrmidon '75 manual by Ward Cunningham. They are subject to tweaking :)

### Control and Movement
Objects in the system move "in real time", according to simple Newtonian kinematics of constant acceleration.\
Your vessel has a position, heading (velocity vector), acceleration, agenda of pending orders, and authcode (required to add orders.)\
You control your vessel by adding orders to it. These orders will be carried out at a given time and will change the ship's acceleration.
In fact, this is the only order you can give your ship. When the order is carried out, your ship's engines will begin to accelerate as ordered, 
instantly setting the ship's acceleration to the given vector.

### Conventions and Constraints
All dimensions are in terms of kilometers, hours, kilometers/hour, or combinations of these.\
No vessel can accelerate with a greater magnitude than 1.6e7 km/hr/hr. Accelerations will automatically be snipped to this amount.\
Vessels can travel at speeds up to approximately lightspeed, specifically 1079251200 km/hr, and velocities will automatically be snipped to this amount.

### Commands
#### Controlling and monitoring your ship
The parser recognizes two types of commands. *Orders*, which affect the ship, are added to a ship's pending orders, and carried out at a certain time. *Requests* are requests for data on the ship or its environment, and return a report immediately.

Some orders require a time or time interval to be specified in the command. Times specified in other commands will be ignored. If a time isn't specified in an order, the current real-life time is used.

Orders:
- burn *x y z*
    
    `burn` sets the ship's acceleration to [*x*, *y*, *z*]. A time or interval has to be specified somewhere else in the command.
    Examples:
    ```
    in 3 hours burn 0 0 0
    burn 4.04 0 0 at 2022-12-28 17:55
    ```

- cancel *order_id*

    `cancel` cancels the order with the given ID number.

Requests:
- `scan` lists all objects in the system, and their kinematics and allegiance.
- `summary` lists all events that have happened in the system since game start.
- `agenda` lists the pending orders for your vessel.

#### Details
Time intervals are recognized by the keywords `minutes`, `hours`, and `days`. Exact dates must follow the keyword `at`. Exact dates must be written as *year-month-day hour:minute:second*, all integers, with zero-padding and in 24-hour time. For example, 3am on January 1, 2022 would be `at 2022-01-01 03:00:00`. This will hopefully be made more flexible in the future.

Each command is a single line of text.
Words in a command are separated by spaces. The parser counts commas, periods, and other clause punctuation as part of the word, so you probably want to avoid them.

A command may only have a single verb. The verb can appear anywhere in the command, as long as any other details it expects are in the right place.
