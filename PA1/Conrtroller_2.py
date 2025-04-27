"""
This is a POX controller.
"""
from pox.core import core
import pox
log = core.getLogger()
import pox.openflow.libopenflow_01 as of
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.topo import Topo
from pox.lib.packet.ethernet import ethernet, ETHER_BROADCAST
from pox.lib.packet.arp import arp
from pox.lib.packet.vlan import vlan
from pox.lib.addresses import IPAddr, EthAddr
from pox.lib.util import dpid_to_str, str_to_bool
from pox.lib.recoco import Timer
from pox.lib.revent import EventHalt

import pox.openflow.libopenflow_01 as of


class Controller(object):
    
    status = True
    macToPort= {"00:00:00:00:00:01" : 1, 
                "00:00:00:00:00:02" : 2, 
                "00:00:00:00:00:03" : 3, 
                "00:00:00:00:00:04" : 4, 
                "00:00:00:00:00:05" : 5, 
                "00:00:00:00:00:06" : 6}
    IPtoPort= {"10.0.0.1" : 1, 
                "10.0.0.2" : 2, 
                "10.0.0.3" : 3, 
                "10.0.0.4" : 4, 
                "10.0.0.5" : 5, 
                "10.0.0.6" : 6}
    """ 
    This is a controller class that handles packets.
    
    It takes in an incoming packet, and decides what to do with it.
    """
    def __init__(self, connection):
        # Initialize the connection from this controller to the switch.
        self.connection = connection

        # Add a listener to the connection so that when a packet comes in to the switch, the controller is notified.
        connection.addListeners(self)

        core.openflow.addListenerByName("PacketIn", self.handle_PacketIn)

        # Log the initializer.
        log.info("Initializing the controller.")


    def handle_PacketIn(self, event):

        """
        This method handles the packets that come into the controller.
        When a packet is sent to the controller, it actually comes in as an event. 
        Then you have to parse that event to turn it into a packet.
        """
        # Extracting the packet from the event.
        packet = event.parsed
        # Checking if the packet is an arp request packet.
        arp_packet = packet.find('arp')
        if arp_packet: 

            log.info("ARP packet received by controller from port: %s", str(event.port))
            log.info("ARP packet's src: %s dst: %s", 
            str(arp_packet.protosrc), str(arp_packet.protodst))
            self.handle_ARP_Packet(event, arp_packet)      
            
        else:
            # If not arp packet, check if its an ICMP packet.
            icmp_pkt = packet.find('icmp')
            if icmp_pkt:
                log.info("ICMP packet received by controller from port: %s", str(event.port))
                self.handle_ICMP_packet(event)

        return  
        
    def handle_ARP_Packet(self, event, arp_packet):
        # Getting the port of the event.
        inport = event.port 

        # If the ARP packet is a request, flood the switch and then add a flow to the table.
        if arp_packet.opcode == arp.REQUEST:
            log.info("Port %s's ARP packet is a ARP request. Adding a flow rule to the table.", inport)

            # Creating a match rule for the switch. (e.g. h1-h5)
            msg = of.ofp_flow_mod()
            out_port = 0
            # The incoming port will be the port that this ARP_REQUEST packet came in from.
            msg.match.in_port = inport
            msg.match.dl_type = 0x0800
            msg.match.nw_dst = arp_packet.protodst
            msg.match.nw_src = arp_packet.protosrc
            # If the ARP_REQUEST came in through ports 1-4, then set a rule that sets the dst as 10.0.0.5 or 10.0.0.6.
            if (inport == 1 or inport == 3):
                out_port = 5
                dstAddress = "10.0.0.5"
            if (inport == 2 or inport == 4):
                out_port = 6
                dstAddress = "10.0.0.6"
                msg.actions.append(of.ofp_action_nw_addr.set_dst(IPAddr(dstAddress)))
            if (inport == 5 or inport == 6):
                out_port = self.IPtoPort[str(arp_packet.protodst)]
                msg.actions.append(of.ofp_action_nw_addr.set_src(IPAddr("10.0.0.10")))

            # Telling which port to go out through. (e.g. port 5)
            out_action = of.ofp_action_output(port = out_port)
            msg.actions.append(out_action)
            event.connection.send(msg)

        log.info("Forwarding port %s's ARP packet.", inport)
        # Just check its dst and forward it to the port that dst is based on.
        if (inport == 1 or inport == 3):
            out_port = 5
        if (inport == 2 or inport == 4):
            out_port = 6
        elif (event.port == 5 or event.port == 6):
            out_port = self.IPtoPort[str(arp_packet.protodst)]

        msg = of.ofp_packet_out()
        msg.actions.append(of.ofp_action_output(port = out_port))
        msg.data = event.ofp
        event.connection.send(msg.pack())
        log.info("Port %s's ARP packet forwarded to %s", inport, str(out_port))

        return
        

    def handle_ICMP_packet(self, event):
        log.info("Telling the switch to forward this ICMP Packet to the correct port.")
        # ip_packet = icmp_packet.payload
        icmp_packet = event.parsed
        
        out_port = 0
        # Getting the dst and determining the out port of this ICMP packet.
        if (event.port == 1 or event.port == 3):
            out_port = 5
        if (event.port == 2 or event.port == 4):
            out_port = 6
        elif event.port == 5 or event.port == 6:
            out_port = self.IPtoPort[str(icmp_packet.protodst)]
        
        msg = of.ofp_packet_out(data = event.ofp)
        msg.actions.append(of.ofp_action_output(port = out_port))
        event.connection.send(msg)

def launch():
    """
    This method is called when the controller is set up. It's like a main() method. 
    """
    log.info("Logging launch.")

    def connection_up(event):
        Controller(event.connection)

    # Putting the controller up.
    core.openflow.addListenerByName("ConnectionUp", connection_up)

