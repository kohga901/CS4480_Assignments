#!/bin/bash
FROM ubuntu
RUN apt-get update
RUN apt-get -y install bash iproute2 net-tools tcpdump vim iputils-ping
RUN apt-get clean

# Copy the script and then make it executable.
COPY script.sh /script.sh
RUN chmod +x /script.sh

# Run the script.
CMD ["/script.sh"]


