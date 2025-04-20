# Install the daemon on the specified router and put the corresponding frr.config file.
FROM ubuntu
RUN apt-get update
RUN apt-get -y install bash iproute2 net-tools tcpdump vim iputils-ping
RUN apt-get clean

# Install FRR on this r1 container.
RUN apt -y install curl
RUN apt -y install gnupg
RUN curl -s https://deb.frrouting.org/frr/keys.gpg | \
tee /usr/share/keyrings/frrouting.gpg > /dev/null
RUN apt install lsb-release
RUN FRRVER="frr-stable"
RUN echo deb ’[signed-by=/usr/share/keyrings/frrouting.gpg]’ https://deb.frrouting.org/frr \
$(lsb_release -s -c) $FRRVER | tee -a /etc/apt/sources.list.d/frr.list
RUN apt update && apt -y install frr frr-pythontools

# Enable OSPF by putting in the frr.config file inside the FRR.
# First set the ospf=yes inside /etc/frr/daemons
RUN sed -i 's/bgpd=no/ospfd=yes/' /etc/frr/daemons

# Second copy in the r1-frr.conf file into the container's frr.
COPY r3-frr.conf /etc/frr/frr.conf

CMD ["/usr/lib/frr/frrinit.sh", "start"]

