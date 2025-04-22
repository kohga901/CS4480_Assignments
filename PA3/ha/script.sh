#!/bin/bash

# Add a route that goes to hb.
route add -net 10.0.15.0/24 gw 10.0.10.4

# Start the node.
bash