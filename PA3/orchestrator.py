import argparse

def main():
    parser = argparse.ArgumentParser(description="Orchestrator CLI tool")
    
    # Add arguments here
    parser.add_argument('--start', type=str, required=True, help="Sets up the topology, containers, routers and frrouting")
    parser.add_argument('--switchT', type=str, help="Switch traffic between containers")
    
    args = parser.parse_args()
    
    # Handle the arguments
    
if __name__ == "__main__":
    main()