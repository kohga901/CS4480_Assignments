#!/bin/bash

# Keep container running
sed -i 's/ospfd=no/ospfd=yes/' /etc/frr/daemons
exec tail -f /dev/null