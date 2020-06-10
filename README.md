# mir_control
High level python class to control either MiR fleet manager or individual mobile robot

The software communicates with the MiR REST API. 

Credentials have been established for admin user. Should you decide to modify end-user, modify the SHA265 generated key.


Options have been simplified to achieve 4 requests:

1) Provide general information (Location, battery percentage, time remaining, distance to next target, robot name, velocity params)
2) Pause
3) Play
4) Define location

