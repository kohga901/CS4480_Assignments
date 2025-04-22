import argparse
import subprocess
# Khongor Gantumur
# u1389938

# This python file is used to orchestrate the topology and manage the containers and routers.

# HOW TO USE THIS FILE:
# 1. To set up the topology, run:                       python orchestrator.py --setupTopology
# 2. To switch traffic, run:                            python orchestrator.py --switchTraffic N (for northbound) or S (for southbound).
# 3. To restart the topology, run:                      python orchestrator.py --restart
# 4. To issue a ping from host A to host B, run:        python orchestrator.py --ping

# You first need to set it up with the command:         python orchestrator.py --setupTopology
# Then you can switch the traffic with the command:     python orchestrator.py --switchTraffic N or S.
# Then you can issue a ping with the command:           python orchestrator.py --ping.
# [OPTIONAL] Then you can restart the topology with the 
# command:                                              python orchestrator.py --restart

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

def build_topology():
    # Builds the topology, containers, routers and frrouting.
    subprocess.run(["docker", "compose", "up", "--build", "-d"])
    
def switch_traffic(path):
    # Get the interfaces for the routers.
    # Interfaces for router 1
    ip_to_interface = get_interface_ip_map("part1-r1-1")
    interface_of_net_11 = ip_to_interface["10.0.11.4"]
    interface_of_net_14 = ip_to_interface["10.0.14.3"]

    # Interfaces for router 3
    ip_to_interface = get_interface_ip_map("part1-r3-1")
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
        print("Invalid traffic type specified.")

def send_ping():
    # Issues a ping from host A to host B.
    subprocess.run(["docker", "exec", "-it", "part1-ha-1", "ping", "10.0.15.3", "-c", "6"])

def get_interface_ip_map(node):
    ip_to_interface = {}
    # Get the IP address of the interfaces in the node.
    result = subprocess.run(["docker", "exec", node, "ip", "-o", "-4", "addr", "show"], capture_output=True, text=True
)

    # Split the output into lines
    output = result.stdout.strip().split('\n')
    
    # Iterate through each line and extract the interface number and IP address. And store it in the mapping.
    for line in output:
        line_split = line.split()
        interface_number = line_split[1]
        ip_address = line_split[3].split('/')[0]
        ip_to_interface[ip_address] = interface_number

    return ip_to_interface

if __name__ == "__main__":
    main()