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

"""
This is a POX controller. That handles load balancing on a switch in a Round Robin fashion.
"""
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
    # Initializer.
    def __init__(self, connection):
        # Initialize the connection from this controller to the switch.
        self.connection = connection

        # Add a listener to the connection so that when a packet comes in to the switch, the controller is notified.
        connection.addListeners(self)

        core.openflow.addListenerByName("PacketIn", self.handle_PacketIn)

        # Log the initializer.
        log.info("Initializing the controller.")

    # This method handles packets that come in. 
    def handle_PacketIn(self, event):

        """
        This method handles the packets that come into the controller.
        When a packet that doesn't match the flow rules come in, it sends this
        method to one of two methods. ARP handler method or ICMP handler method.
        """
        # Extracting the packet from the event.
        packet = event.parsed
        # Checking if the packet is an arp request packet.
        arp_packet = packet.find('arp')

        if arp_packet: 
            log.info("ARP request received by controller from port: %s", str(event.port))
            log.info("ARP REQUEST's src: %s dst: %s", 
            str(arp_packet.protosrc), str(arp_packet.protodst))
            self.handle_ARP_Packet(event, packet, arp_packet)      
            
        else:
            # If not arp packet, check if its an ICMP packet.
            icmp_pkt = packet.find('icmp')
            if icmp_pkt:
                log.info("ICMP packet received by controller from port: %s", str(event.port))
                self.handle_ICMP_packet(event)

        return  
    # This method builds an arp reply packet and sets the flow rule table.
    def handle_ARP_Packet(self, event, packet, arp_packet):
        # Getting the port of the event.
        inport = event.port 
        # Extracting the packet from the event.
        packet = event.parsed
        # Check if the packet is an ARP REQUEST.
        if (arp_packet.opcode == arp.REQUEST):
            # Build an ARP REPLY packet.
            arp_reply = arp()
            arp_reply.hwtype = arp_packet.hwtype
            arp_reply.prototype = arp_packet.prototype
            arp_reply.hwlen = arp_packet.hwlen
            arp_reply.protolen = arp_packet.protolen
            arp_reply.opcode = arp.REPLY
            arp_reply.hwdst = arp_packet.hwsrc
            arp_reply.protodst = arp_packet.protosrc
            arp_reply.protosrc = arp_packet.protodst

            # If the ARP REQUEST's dst IP is 10.0.0.10 meaning it wants the mac address of 10.0.0.10, then
            # return the mac address of h5 or h6 depending on the bool value called status. (Round Robin).
            if (arp_packet.protodst == IPAddr("10.0.0.10")):
                if (self.status):
                    arp_reply.hwsrc =  EthAddr("00:00:00:00:00:05")
                    self.status = False
                else:
                    arp_reply.hwsrc =  EthAddr("00:00:00:00:00:06")
                    self.status = True

            if (arp_packet.protodst == IPAddr("10.0.0.1")):
                arp_reply.hwsrc = EthAddr("00:00:00:00:00:01")
            if (arp_packet.protodst == IPAddr("10.0.0.2")):
                arp_reply.hwsrc = EthAddr("00:00:00:00:00:02")
            if (arp_packet.protodst == IPAddr("10.0.0.3")):
                arp_reply.hwsrc = EthAddr("00:00:00:00:00:03")
            if (arp_packet.protodst == IPAddr("10.0.0.4")):
                arp_reply.hwsrc = EthAddr("00:00:00:00:00:04")

            # Constructing an ARP REPLY packet.
            e = ethernet(type=packet.type, src=event.connection.eth_addr, dst=arp_packet.hwsrc)
            e.payload = arp_reply

            log.info("Answering ARP that was received from: %s" % (str(arp_reply.protodst)))

            # Sending the arp reply to the switch.
            msg = of.ofp_packet_out()
            msg.data = e.pack()
            msg.actions.append(of.ofp_action_output(port = of.OFPP_IN_PORT))
            msg.in_port = inport
            event.connection.send(msg)

            log.info("ARP Reply sent. The MAC address sent was: %s" % (str(arp_reply.hwsrc)))
            log.info("ARP REPLY's src: %s dst: %s", 
            str(arp_reply.protosrc), str(arp_reply.protodst))
            
            # Creating a match rule for the switch. (e.g. h1-h5)
            msg = of.ofp_flow_mod()

            out_port = 0
            # The incoming port will be the port that this ARP_REQUEST packet came in from.
            msg.match.in_port = inport
            msg.match.dl_type = 0x0800
            msg.match.nw_dst = arp_packet.protodst
            msg.match.nw_src = arp_packet.protosrc


            # If the ARP_REQUEST came in through ports 1-4, then set a rule that sets the dst as 10.0.0.5 or 10.0.0.6.
            if (inport == 1 or inport == 2 or inport == 3 or inport == 4):
                # If status is true, direct all traffic to 10.0.0.6.
                # If status is false, direct all traffic to 10.0.0.5.
                if (self.status):
                    dstAddress = "10.0.0.6"
                else:
                    dstAddress = "10.0.0.5"
                
                # Setting the out port.
                if (dstAddress == "10.0.0.6"):
                    out_port = 6
                else:
                    out_port = 5
                # Set the rule where the dst of the ICMP packet is changed from 10.0.0.10 to h5 or h6.
                msg.actions.append(of.ofp_action_nw_addr.set_dst(IPAddr(dstAddress)))

            # If the ARP_REQUEST came in through ports 5 or 6, then set a rule that sets the src as 10.0.0.10.
            else:
                out_port = self.IPtoPort[str(arp_packet.protodst)]
                msg.actions.append(of.ofp_action_nw_addr.set_src(IPAddr("10.0.0.10")))
            
            # Telling which port to go out through. (e.g. port 5)
            out_action = of.ofp_action_output(port = out_port)
            msg.actions.append(out_action)
            event.connection.send(msg)
            log.info("Matching on inport: %s, nw_dst: %s, nw_src: %s" % (str(inport),
                         str(arp_packet.protodst), str(arp_packet.protosrc)))

            return
        
    # This method handles ICMP packets that come through. Basically just tells the switch to use the
    # flow table rules to handle the ICMP packet.
    def handle_ICMP_packet(self, event):
        log.info("Telling the switch to forward this ICMP Packet to the correct port.")

        icmp_packet = event.parsed
        # Building message.
        msg = of.ofp_packet_out(data = event.ofp)
        msg.actions.append(of.ofp_action_output(port = of.OFPP_TABLE))
        event.connection.send(msg)
        log.info("ICMP packet forwarded: inport: %s, src: %s, dst: %s", event.port, 
         str(icmp_packet.payload.srcip), str(icmp_packet.payload.dstip))

def launch():
    """
    This method is called when the controller is set up. It's like a main() method. 
    """
    log.info("Logging launch.")

    def connection_up(event):
        Controller(event.connection)

    # Putting the controller up.
    core.openflow.addListenerByName("ConnectionUp", connection_up)

