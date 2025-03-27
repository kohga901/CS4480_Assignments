"""
This is a POX controller.
"""
from pox.core import core
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

log = core.getLogger()

class Controller(object):
    """ 
    This is a controller class that handles packets.
    
    It takes in an incoming packet, and decides what to do with it.
    """
def __init__(self, connection):
    # Initialize the connection from this controller to the switch.
    self.connection = connection

    # Should I make a forwarding table here?

    # Add a listener to the connection so that when a packet comes in to the switch, the controller is notified.
    connection.addListeners(self)

    # Log the initializer.
    log.debug("Initializing the controller.")


def handle_ARP_Packets(self, event):
    """
    This method handles the packets that come into the controller.
    When a packet is sent to the controller, it actually comes in as an event. 
    Then you have to parse that event to turn it into a packet.
    """
    # Getting the port of the event.
    inport = event.port 
    # Extracting the packet from the event.
    packet = event.parsed
    # Checking if the packet is an arp request packet.
    arp_packet = packet.find('arp')
    if arp_packet:
        log.debug("ARP request received by controller.")

    status = True

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

        if (arp_packet.protodst == IPAddr("10.0.0.10")):
            if (status):
                # check if just assigning it like this works or not
                arp_reply.hwsrc =  EthAddr("00:00:00:00:00:05")
        if (arp_packet.protodst == IPAddr("10.0.0.1")):
            arp_reply.hwsrc = EthAddr("00:00:00:00:00:01")
        if (arp_packet.protodst == IPAddr("10.0.0.2")):
            arp_reply.hwsrc = EthAddr("00:00:00:00:00:02")
        if (arp_packet.protodst == IPAddr("10.0.0.3")):
            arp_reply.hwsrc = EthAddr("00:00:00:00:00:03")
        if (arp_packet.protodst == IPAddr("10.0.0.4")):
            arp_reply.hwsrc = EthAddr("00:00:00:00:00:04")
       
        e = ethernet(type=packet.type, src=event.connection.eth_addr,
                        dst=arp_packet.hwsrc)
        e.payload = arp_reply

        log.info("Answering ARP for %s" % (str(arp_reply.protosrc)))
        msg = of.ofp_packet_out()
        msg.data = e.pack()
        msg.actions.append(of.ofp_action_output(port =
                                                of.OFPP_IN_PORT))
        msg.in_port = inport
        event.connection.send(msg)

        add_flow_rules(self)

    # msg = of.ofp_flow_mod()
    # msg.match.in_port = 1
    # msg.match.dl_type = 0x0800
    # msg.match.nw_dst = IPAddr("10.0.0.1")
    # msg.match.nw_src = IPAddr("10.0.0.10")
    # msg.actions.append(of.ofp_action_nw_addr.set_dst(IPAddr("10.0.0.5")))

    # self.connection.send(msg)
    # msg = of.ofp_flow_mod()
    # msg.match.in_port = 1
    # msg.match.dl_type = 0x0800
    # msg.match.nw_dst = IPAddr("10.0.0.5")
    # msg.match.nw_src = IPAddr("10.0.0.1")
    # msg.actions.append(of.ofp_action_nw_addr.set_src(IPAddr("10.0.0.10")))

    # self.connection.send(msg)

def add_flow_rules(self):
    msg = of.ofp_flow_mod()
    msg.match.in_port = 1
    msg.match.dl_type = 0x0800
    msg.match.nw_dst = IPAddr("10.0.0.1")
    msg.match.nw_src = IPAddr("10.0.0.10")
    msg.actions.append(of.ofp_action_nw_addr.set_dst(IPAddr("10.0.0.5")))

    self.connection.send(msg)
    msg = of.ofp_flow_mod()
    msg.match.in_port = 1
    msg.match.dl_type = 0x0800
    msg.match.nw_dst = IPAddr("10.0.0.5")
    msg.match.nw_src = IPAddr("10.0.0.1")
    msg.actions.append(of.ofp_action_nw_addr.set_src(IPAddr("10.0.0.10")))

    self.connection.send(msg)

def launch():
    """
    This method is called when the controller is set up. It's like a main __init__ method. 
    """

    # Putting the controller up.
    core.registerNew(Controller)  