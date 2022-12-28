# Dotwar/Myrmidon Manual
Welcome to Dotwar. You are a dot, somewhere in the vicinity of dot Earth.\
Specifically, your spacecraft is a dot, traversing 3d space in your stead.\
If you are an attacker, your mission is to capture Earth.\
If you are a defender, your mission is to eliminate all attackers.

## Gameplay
### Conventions and Constraints
All dimensions are in terms of kilometers, hours, kilometers/hour, or combinations of these.\
No vessel can accelerate with a greater magnitude than 1.6e7 km/hr/hr. Accelerations will automatically be snipped to this amount.\
Vessels can travel at speeds up to approximately lightspeed, specifically 1079251200 km/hr, and velocities will automatically be snipped to this amount.

### Control and Movement
Objects in the system move "in real time", according to simple Newtonian kinematics of constant acceleration.\
You control your vessel by adding orders to it. These orders will be carried out at a given time and will change the ship's acceleration.
In fact, this is the only order you can give your ship. When the order is carried out, your ship's engines will begin to accelerate as ordered, 
instantly setting the ship's acceleration to the given vector.

### Capture and Elimination
The attackers' goal is to capture Earth. Earth is instantly captured if any attacker is within 1.6e7 km or it.\
The defenders' goal is to eliminate all defenders. An attacker is intantly destroyed if a defender gets within 1.12e7 km of it (70% of the capture radius.)\
If all attackers are eliminated, the defenders win.\
These numbers are slightly modified from the myrmidon '75 manual by Ward Cunningham. They are subject to tweaking :)
