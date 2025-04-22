#!/bin/bash
FROM ubuntu
RUN apt-get update
RUN apt-get -y install bash iproute2 net-tools tcpdump vim iputils-ping
RUN apt-get clean

RUN apt -y install curl
RUN apt -y install gnupg
RUN curl -s https://deb.frrouting.org/frr/keys.gpg | \
tee /usr/share/keyrings/frrouting.gpg > /dev/null
RUN apt install lsb-release
RUN FRRVER="frr-stable"
RUN echo deb "[signed-by=/usr/share/keyrings/frrouting.gpg]" https://deb.frrouting.org/frr
RUN $(lsb_release -s -c) $FRRVER | tee -a /etc/apt/sources.list.d/frr.list
RUN apt update && apt -y install frr frr-pythontools

# Set the ospfd to yes in this script because the daemons get reset after the container initializes.
COPY ./daemons /etc/frr/daemons

# Enable OSPF by putting in the frr.config file inside the FRR.
COPY ./r2-frr.conf /etc/frr/frr.conf

# Copy the script and then make it executable.
COPY script.sh /script.sh
RUN chmod +x /script.sh

# Run the script.
CMD ["/script.sh"]


