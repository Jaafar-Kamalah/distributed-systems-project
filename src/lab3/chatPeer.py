#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# Distributed Systems (TDDD25)
# -----------------------------------------------------------------------------
# Author: Sergiu Rafiliu (sergiu.rafiliu@liu.se)
# Modified: 31 July 2013
#
# Copyright 2012 Linkoping University
# -----------------------------------------------------------------------------

"""A simple chat client.

This chat client retains a list of peers so that it can send messages
to each of them.
"""

import sys
import random
import socket
import argparse

sys.path.append("../modules")
from Common import orb
from Common.nameServiceLocation import name_service_address
from Common.objectType import object_type

from Server.peerList import PeerList

# -----------------------------------------------------------------------------
# Initialize and read the command line arguments
# -----------------------------------------------------------------------------

rand = random.Random()
rand.seed()
description = """Chat peer."""
parser = argparse.ArgumentParser(description=description)
parser.add_argument(
    "-p", "--port", metavar="PORT", dest="port", type=int,
    default=rand.randint(1, 10000) + 40000, choices=range(40001, 50000),
    help="Set the port to listen to. Must be in the range 40001 .. 50000."
         "The default value is chosen at random."
)
parser.add_argument(
    "-t", "--type", metavar="TYPE", dest="type", default=object_type,
    help="Set the type of the client."
)
opts = parser.parse_args()

local_port = opts.port
client_type = opts.type
assert client_type != "object", "Change the object type to something unique!"

# -----------------------------------------------------------------------------
# Auxiliary classes
# -----------------------------------------------------------------------------


class Client(orb.Peer):

    """Chat client class."""

    def __init__(self, local_address, ns_address, cient_type):
        """Initialize the client."""
        orb.Peer.__init__(self, local_address, ns_address, client_type)
        self.peer_list = PeerList(self)
        self.dispatched_calls = {
            "register_peer":     self.peer_list.register_peer,
            "unregister_peer":   self.peer_list.unregister_peer,
            "display_peers":     self.peer_list.display_peers
        }
        orb.Peer.start(self)
        self.peer_list.initialize()

    # Public methods

    def destroy(self):
        orb.Peer.destroy(self)
        self.peer_list.destroy()

    def __getattr__(self, attr):
        """Forward calls are dispatched here."""
        if attr in self.dispatched_calls:
            return self.dispatched_calls[attr]
        else:
            raise AttributeError(
                "Client instance has no attribute '{}'".format(attr))

    def print_message(self, from_id, msg):
        print("Received a message from {}: {}".format(from_id, msg))

    def send_message(self, to_id, msg):
        try:
            self.peer_list.peer(to_id).print_message(self.id, msg)
        except Exception:
            print(("Cannot send messages to {}."
                   "Make sure it is in the list of peers.").format(to_id))

# -----------------------------------------------------------------------------
# The main program
# -----------------------------------------------------------------------------

# Initialize the client object.
local_address = (socket.getfqdn(), local_port)
p = Client(local_address, name_service_address, client_type)


def menu():
    print("""\
Choose one of the following commands:
    l                       ::  display the peer list,
    <PEER_ID> : <MESSAGE>   ::  send <MESSAGE> to <PEER_ID>,
    h                       ::  print this menu,
    q                       ::  exit.\
""")

command = ""
cursor = "{}({})> ".format(p.type, p.id)
menu()
while command != "q":
    try:
        sys.stdout.write(cursor)
        command = input()
        if command == "l":
            p.display_peers()
        elif command == "h":
            menu()
        else:
            pos = command.find(":")
            if pos > -1 and command[0:pos].strip().isdigit():
                # We have a command to send a message to someone.
                to_id = int(command[0:pos])
                msg = command[pos + 1:]
                p.send_message(to_id, msg)
    except KeyboardInterrupt:
        break

# Kill our peer object.
p.destroy()
