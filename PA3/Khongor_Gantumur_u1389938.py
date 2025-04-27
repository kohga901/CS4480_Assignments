import argparse
import subprocess
# Khongor Gantumur
# u1389938

# This python file is used to orchestrate the topology and manage the containers and routers.

# HOW TO USE THIS FILE:
# 1. To set up the topology, run:                       python orchestrator.py --setupTopology
# NOTE: After setup is complete, wait 30 seconds or so for the ospf to share their routing tables. Running ping too early results in packet loss.
# 2. To switch traffic, run:                            python orchestrator.py --switchTraffic N (for northbound) or S (for southbound).
# 3. To restart the topology, run:                      python orchestrator.py --restart
# 4. To issue a ping from host A to host B, run:        python orchestrator.py --ping

# You first need to set it up with the command:         python orchestrator.py --setupTopology
# Then you can switch the traffic with the command:     python orchestrator.py --switchTraffic N or S.
# Then you can issue a ping with the command:           python orchestrator.py --ping.
# [OPTIONAL] Then you can restart the topology with the 
# command:                                              python orchestrator.py --restart

# Main function to handle command line arguments and orchestrate the topology.
def main():
    parser = argparse.ArgumentParser()
    
    # Add optional arguments
    parser.add_argument('--setupTopology', action='store_true', help="Sets up the topology, containers, routers and frrouting")
    
    # Add restart argument
    parser.add_argument('--restart', action='store_true', help="Restarts the topology.")

    # Add switchTraffic argument
    parser.add_argument('--switchTraffic', choices=['N', 'S'], help='This flag must be followed by N or S. N for northbound trafic and S for southbound traffic.')
    
    # Add ping argument
    parser.add_argument('--ping', action='store_true', help="Issues a ping from host A to host B.")

    args = parser.parse_args()
    
    # Handle the arguments
    if args.setupTopology:
        build_topology()
    elif args.restart:
        subprocess.run(["docker", "compose", "down"])
        build_topology()
        
    elif args.switchTraffic:
        if args.switchTraffic == "N":
            switch_traffic("N")
        elif args.switchTraffic == "S":
            switch_traffic("S")
    elif args.ping:
        send_ping()
    else:
        print("No valid arguments provided. Use --help for more information.")


# Function to build the topology, containers, routers and frrouting.
def build_topology():
    # Builds the topology, containers, routers and frrouting.
    subprocess.run(["docker", "compose", "up", "--build", "-d"])

# Switches the traffic between the containers based on the specified path (S or N).
def switch_traffic(path):
    # Get the interfaces for the routers.
    # Interfaces for router 1
    ip_to_interface = get_interfaces_with_the_ip("part1-r1-1")
    interface_of_net_11 = ip_to_interface["10.0.11.4"]
    interface_of_net_14 = ip_to_interface["10.0.14.3"]

    # Interfaces for router 3
    ip_to_interface = get_interfaces_with_the_ip("part1-r3-1")
    interface_of_net_12 = ip_to_interface["10.0.12.3"]
    interface_of_net_13 = ip_to_interface["10.0.13.4"]

    # Switches the traffic based on the specified path.
    if path == "S":
        subprocess.run(["docker", "exec", "-it", "part1-r1-1", "vtysh", "-c", "configure terminal", "-c", "interface" + " " + interface_of_net_11, "-c", "ip ospf cost 10", "-c", "end"])
        subprocess.run(["docker", "exec", "-it", "part1-r1-1", "vtysh", "-c", "configure terminal", "-c", "interface" + " " + interface_of_net_14, "-c", "ip ospf cost 5", "-c", "end"])
        subprocess.run(["docker", "exec", "-it", "part1-r3-1", "vtysh", "-c", "configure terminal", "-c", "interface" + " " + interface_of_net_12, "-c", "ip ospf cost 10", "-c", "end"])
        subprocess.run(["docker", "exec", "-it", "part1-r3-1", "vtysh", "-c", "configure terminal", "-c", "interface" + " " + interface_of_net_13, "-c", "ip ospf cost 5", "-c", "end"])

    elif path == "N":
        subprocess.run(["docker", "exec", "-it", "part1-r1-1", "vtysh", "-c", "configure terminal", "-c", "interface" + " " + interface_of_net_11, "-c", "ip ospf cost 5", "-c", "end"])
        subprocess.run(["docker", "exec", "-it", "part1-r1-1", "vtysh", "-c", "configure terminal", "-c", "interface" + " " + interface_of_net_14, "-c", "ip ospf cost 10", "-c", "end"])
        subprocess.run(["docker", "exec", "-it", "part1-r3-1", "vtysh", "-c", "configure terminal", "-c", "interface" + " " + interface_of_net_12, "-c", "ip ospf cost 5", "-c", "end"])
        subprocess.run(["docker", "exec", "-it", "part1-r3-1", "vtysh", "-c", "configure terminal", "-c", "interface" + " " + interface_of_net_13, "-c", "ip ospf cost 10", "-c", "end"])
    else:
        print("Invalid traffic direction specified. Traffic direction must only be N or S.")

# Function to issue a ping from host A to host B.
def send_ping():
    # Issues a ping from host A to host B.
    subprocess.run(["docker", "exec", "-it", "part1-ha-1", "ping", "10.0.15.3", "-c", "6"])

# Function to get the interface IP mapping for a given node.
def get_interfaces_with_the_ip(node):
    # Initialize the dictionary for mapping ip addresses to their corresponding interfaces on the routers.
    ip_to_interface = {}
    # Get the IP address of the interfaces in the node.
    result = subprocess.run(["docker", "exec", node, "ip", "-o", "-4", "addr", "show"], capture_output=True, text=True)

    # Split the output into lines
    output = result.stdout
    output = output.strip()
    output = output.split('\n')
    
    # Iterate through each line of the output and extract the interface numbers and IP addresses. 
    # And then store it in the dictionary.
    for line in output:
        # Split the line with whitespace.
        split_line = line.split()
        # Get the interface number from the line where the second item is the eth
        eth_number = split_line[1]
        # Get the IP address from the line.
        ip_address = split_line[3]
        ip_address = ip_address.split('/')[0]
        # Store the ethernet number with the corresponing ip address.
        ip_to_interface[ip_address] = eth_number

    return ip_to_interface

if __name__ == "__main__":
    main()