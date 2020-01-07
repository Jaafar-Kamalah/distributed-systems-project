#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# Distributed Systems (TDDD25)
# -----------------------------------------------------------------------------
# Author: Sergiu Rafiliu (sergiu.rafiliu@liu.se)
# Modified: 28 January 2015
#
# Copyright 2012-2015 Linkoping University
# -----------------------------------------------------------------------------

"""A simple peer implementation.

This implementation simply connects to the name service and asks for the
list of peers.

"""

import sys
import random
import socket
import argparse

sys.path.append("../modules")
from Common import orb
from Common.nameServiceLocation import name_service_address
from Common.objectType import object_type

# -----------------------------------------------------------------------------
# Initialize and read the command line arguments
# -----------------------------------------------------------------------------

rand = random.Random()
rand.seed()
description = """Simple peer."""
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

    def __init__(self, local_address, ns_address, client_type):
        """Initialize the client."""
        orb.Peer.__init__(self, local_address, ns_address, client_type)
        orb.Peer.start(self)

    # Public methods

    def destroy(self):
        """Destroy the peer object."""
        orb.Peer.destroy(self)

    def display_peers(self):
        """Display all the peers in the list."""
        peers = self.name_service.require_all(self.type)
        print("List of peers of type '{0}':".format(self.type))
        for pid, paddr in peers:
            print("    id: {:>2}, address: {}".format(pid, tuple(paddr)))

# -----------------------------------------------------------------------------
# The main program
# -----------------------------------------------------------------------------

# Initialize the client object.
local_address = (socket.getfqdn(), local_port)
p = Client(local_address, name_service_address, client_type)

print("""\
This peer:
    id: {:>2}, address: {}""".format(p.id, p.address))

# Print the list of peers.
p.display_peers()

# Waiting for a key press.
sys.stdout.write("Waiting for a key press...")
input()

# Kill our peer object.
p.destroy()
