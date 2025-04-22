#!/bin/bash

# Add a route that goes to ha.
route add -net 10.0.10.0/24 gw 10.0.15.4

# Keep container running
bash