from pox.core import core
import pox.openflow.libopenflow_01 as of
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.topo import Topo

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


def send_Packet(self, packet, out_port):
    """
    This method basically sends the switch a message that contains a packet and a port. 
    And tells the switch to send that packet through the specified port.
    """
    # Telling that this message is supposed to go out of the switch.
    msg = of.ofp_packet_out()

    # Inserting the packet inside the message.
    msg.data = packet

    # Assingning what port the message will go out through from the switch.
    action = of.ofp_action_output(port = out_port)
    
    # Inserting the action into the message.
    msg.actions.append(action)

    # Finally, sending the message to the switch.
    self.connection.send(msg)


def handle_PacketIn(self, event):
    """
    This method handles the packets that come into the controller.
    When a packet is sent to the controller, it actually comes in as an event. 
    Then you have to parse that event to turn it into a packet.
    """
    # Extracting the packet from the event.
    packet = event.ofp
    log.debug("A packet just came in:\n" + packet)

    # Send the packet to a method that decides what to do with that packet.
    switch(packet)


def switch(self, packet):
    """
    This takes in a packet and decides what to do with it. If the packet's destination is at 10.0.0.10, 
    it checks if the bool value is true or false.
    If its true, it sets the destination as 10.0.0.5 and sets the outgoing port for this packet as 5.
    If its false, it sets the destination as 10.0.0.6 and sets the outgoing port for this packet as 6.
    Then it sends the packet to the send_Packet method.
    """
    # Just for testing purposes, this method is going to flood this packet on the switch.
    send_Packet(packet, of.OFPP_FLOOD)


def launch():
    """
    This method is called when the controller is set up. It's like a main __init__ method. 
    """
    # Putting the controller up.
    core.openflow.addListenerByName("PacketIn", handle_PacketIn)