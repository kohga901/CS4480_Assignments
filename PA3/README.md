Author: Khongor Gantumur

This is the README file for the orchestrator app. 

HOW TO USE APP:

The setupTopology command must be run first. Then the switchTraffic command must be run. Because 
on topology startup, the weights on every interface is set to 5. So a weight must be set on either 
the North or South path in order to ping. Then the ping command can be run. 

The app has 4 commands: 
orchestrator.py --setupTopology
Starts the topology, sets up all containers, installs and configures frr, and starts the containers.

orchestrator.py --switchTraffic [N or S]
Sets the traffic to North (r2) or South (r4) depending on the argument passed. 
EXAMPLES: orchestrator.py --switchTraffic N
          orchestrator.py --switchTraffic S

orchestrator.py --ping
Issues 6 pings from host A to host B.

orchestrator.py --restart
Restarts the topology by running "compose down" and then "compose up --build -d".





