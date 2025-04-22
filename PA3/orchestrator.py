import argparse

def main():
    parser = argparse.ArgumentParser()
    
    # Add optional arguments
    parser.add_argument('--setupTopology', type=str, help="Sets up the topology, containers, routers and frrouting")
    parser.add_argument('--switchTraffic', type=str, help="Switch traffic between containers")
    
    args = parser.parse_args()
    
    # Handle the arguments
    if args.setupTopology:
        build_topology()
    elif args.switchTraffic:
        switch_traffic(args.switchTraffic)
    else:
        print("No valid arguments provided. Use --help for more information.")

def build_topology():
    # Function to build the topology
    pass
    
def switch_traffic():
# Function to switch traffic between containers
    if traffic_type == "container1":
        # Switch traffic to container 1
        pass
    elif traffic_type == "container2":
        # Switch traffic to container 2
        pass
    else:
        print("Invalid traffic type specified.")


if __name__ == "__main__":
    main()