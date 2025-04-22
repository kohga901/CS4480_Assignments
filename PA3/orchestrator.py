import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser()
    
    # Add optional arguments
    parser.add_argument('--setupTopology', action='store_true', help="Sets up the topology, containers, routers and frrouting")
    parser.add_argument('--switchTraffic', type=str, help="Switch traffic between containers")
    parser.add_argument('--ping', action='store_true', help="Issues a ping from host A to host B.")

    args = parser.parse_args()
    
    # Handle the arguments
    if args.setupTopology:
        if args.setupTopology:
            build_topology()
        
    if args.switchTraffic:
        if args.switchTraffic == "N":
            switch_traffic("N")
        elif args.switchTraffic == "S":
            switch_traffic("S")
    if args.ping:
        send_ping()
    else:
        print("No valid arguments provided. Use --help for more information.")

def build_topology():
    # Builds the topology, containers, routers and frrouting.
    subprocess.run(["docker", "compose", "up", "--build", "-d"])
    
def switch_traffic(path):
    # Switches the traffic based on the specified path.
    if path == "N":
        subprocess.run(["docker", "exec", "-it", "part1-r2-1", "vtysh", "-c", "configure terminal", "-c", "interface eth0", "-c", "ip ospf cost 10", "-c", "end"])
        subprocess.run(["docker", "exec", "-it", "part1-r2-1", "vtysh", "-c", "configure terminal", "-c", "interface eth1", "-c", "ip ospf cost 10", "-c", "end"])
        subprocess.run(["docker", "exec", "-it", "part1-r4-1", "vtysh", "-c", "configure terminal", "-c", "interface eth0", "-c", "ip ospf cost 5", "-c", "end"])
        subprocess.run(["docker", "exec", "-it", "part1-r4-1", "vtysh", "-c", "configure terminal", "-c", "interface eth1", "-c", "ip ospf cost 5", "-c", "end"])
    elif path == "S":
        subprocess.run(["docker", "exec", "-it", "part1-r4-1", "vtysh", "-c", "configure terminal", "-c", "interface eth0", "-c", "ip ospf cost 10", "-c", "end"])
        subprocess.run(["docker", "exec", "-it", "part1-r4-1", "vtysh", "-c", "configure terminal", "-c", "interface eth1", "-c", "ip ospf cost 10", "-c", "end"])
        subprocess.run(["docker", "exec", "-it", "part1-r2-1", "vtysh", "-c", "configure terminal", "-c", "interface eth0", "-c", "ip ospf cost 5", "-c", "end"])
        subprocess.run(["docker", "exec", "-it", "part1-r2-1", "vtysh", "-c", "configure terminal", "-c", "interface eth1", "-c", "ip ospf cost 5", "-c", "end"])
    else:
        print("Invalid traffic type specified.")
def send_ping():
    # Issues a ping from host A to host B.
    subprocess.run(["docker", "exec", "-it", "part1-ha-1", "ping", "10.0.15.3", "-c", "5"])

if __name__ == "__main__":
    main()