#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# Distributed Systems (TDDD25)
# -----------------------------------------------------------------------------
# Author: Sergiu Rafiliu (sergiu.rafiliu@liu.se)
# Modified: 1 February 2015
#
# Copyright 2012-2015 Linkoping University
# -----------------------------------------------------------------------------

"""This is an implementation of a server that reads and writes data to
a database.

This server is one in a group of servers that all replicate the same
data, so they implement 'read any write all' protocol.

"""

import sys
import random
import socket
import argparse

sys.path.append("../modules")
from Common import orb
from Common.nameServiceLocation import name_service_address
from Common.objectType import object_type

from Server import database
from Server.peerList import PeerList
from Server.Lock.distributedLock import DistributedLock
from Server.Lock.distributedReadWriteLock import DistributedReadWriteLock

# -----------------------------------------------------------------------------
# Initialize and read the command line arguments
# -----------------------------------------------------------------------------

rand = random.Random()
rand.seed()
description = """Database server replica. """
parser = argparse.ArgumentParser(description=description)
parser.add_argument(
    "-p", "--port", metavar="PORT", dest="port", type=int,
    default=rand.randint(1, 10000) + 40000, choices=range(40001, 50000),
    help="Set the port to listen to. Values in [40001, 50000]. "
         "The default value is chosen at random."
)
parser.add_argument(
    "-t", "--type", metavar="TYPE", dest="type", default=object_type,
    help="Set the type of the client."
)
parser.add_argument(
    "-f", "--file", metavar="FILE", dest="file", default="dbs/fortune.db",
    help="Set the database file. Default: dbs/fortune.db."
)
opts = parser.parse_args()

local_port = opts.port
db_file = opts.file
server_type = opts.type
assert server_type != "object", "Change the object type to something unique!"


# -----------------------------------------------------------------------------
# Auxiliary classes
# -----------------------------------------------------------------------------


class Server(orb.Peer):

    """Distributed mutual exclusion client class."""

    def __init__(self, local_address, ns_address, server_type, db_file):
        """Initialize the client."""

        orb.Peer.__init__(self, local_address, ns_address, server_type)
        self.peer_list = PeerList(self)
        self.distributed_lock = DistributedLock(self, self.peer_list)
        self.drwlock = DistributedReadWriteLock(self.distributed_lock)
        self.db = database.Database(db_file)
        self.dispatched_calls = {
            "display_peers":      self.peer_list.display_peers,
            "acquire":            self.distributed_lock.acquire,
            "release":            self.distributed_lock.release,
            "request_token":      self.distributed_lock.request_token,
            "obtain_token":       self.distributed_lock.obtain_token,
            "display_status":     self.distributed_lock.display_status
        }
        orb.Peer.start(self)
        self.peer_list.initialize()
        self.distributed_lock.initialize()

    # Public methods

    def destroy(self):
        orb.Peer.destroy(self)
        self.distributed_lock.destroy()
        self.peer_list.destroy()

    def __getattr__(self, attr):
        """Forward calls are dispatched here."""

        if attr in self.dispatched_calls:
            return self.dispatched_calls[attr]
        else:
            raise AttributeError(
                "Client instance has no attribute '{0}'".format(attr))

    # Public methods

    def read(self):
        """Read a fortune from the database."""

        #
        # Your code here.
        #
        pass

    def write(self, fortune):
        """Write a fortune to the database.

        Obtain the distributed lock and call all other servers to write
        the fortune as well. Call their 'write_local' as they cannot
        attempt to obtain the distributed lock when writing their
        copies.

        """

        #
        # Your code here.
        #
        pass

    def write_local(self, fortune):
        """Write a fortune to the database.

        This method is called only by other servers once they've
        obtained the distributed lock.

        """

        self.drwlock.write_acquire_local()
        try:
            self.db.write(fortune)
        finally:
            self.drwlock.write_release_local()

    def register_peer(self, pid, paddr):
        """Register a server peer in this server's peer list."""

        self.peer_list.register_peer(pid, paddr)
        self.distributed_lock.register_peer(pid)

    def unregister_peer(self, pid):
        """Remove a server peer from this server's peer list."""

        self.peer_list.unregister_peer(pid)
        self.distributed_lock.unregister_peer(pid)

# -----------------------------------------------------------------------------
# The main program
# -----------------------------------------------------------------------------

# Initialize the client object.
local_address = (socket.getfqdn(), local_port)
p = Server(local_address, name_service_address, server_type, db_file)


def menu():
    print("""\
Choose one of the following commands:
    l  ::  list peers,
    s  ::  display status,
    h  ::  print this menu,
    q  ::  exit.\
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
        elif command == "s":
            p.display_status()
        elif command == "h":
            menu()
    except KeyboardInterrupt:
        break
    except Exception as e:
        # Catch all errors to keep on running in spite of all errors.
        print("An error has occurred: {}.".format(e))

# Kill our peer object.
p.destroy()
