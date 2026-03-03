# -----------------------------------------------------------------------------
# Distributed Systems (TDDD25)
# -----------------------------------------------------------------------------
# Author: Sergiu Rafiliu (sergiu.rafiliu@liu.se)
# Modified: 30 January 2015
#
# Copyright 2012-2015 Linkoping University
# -----------------------------------------------------------------------------

"""Class implementing a distributed version of ReadWriteLock."""

import threading
from . import readWriteLock


class DistributedReadWriteLock(readWriteLock.ReadWriteLock):

    """Distributed version of ReadWriteLock."""

    def __init__(self, distributed_lock):
        readWriteLock.ReadWriteLock.__init__(self)
        # Create a distributed lock
        self.distributed_lock = distributed_lock
        self.locking_lock = threading.Lock()

    # Public methods

    def write_acquire(self):
        """Acquire the rights to write into the database.

        Override the write_acquire method to include obtaining access
        to the rest of the peers.

        """
        # The locking_lock is to make sure distributed_lock and local_lock are aquired in unison.
        # Without it the same server could call write from two different clients, they would both 
        # aquire distributed_lock but the second thread would block on the local_lock. Once the first 
        # thread releases it could give away the token while the second thread enters the critical section.
        self.locking_lock.acquire()
        self.distributed_lock.acquire()
        readWriteLock.ReadWriteLock.write_acquire(self)

    def write_release(self):
        """Release the rights to write into the database.

        Override the write_release method to include releasing access
        to the rest of the peers.

        """
        self.distributed_lock.release()
        readWriteLock.ReadWriteLock.write_release(self)
        self.locking_lock.release()

    def write_acquire_local(self):
        readWriteLock.ReadWriteLock.write_acquire(self)

    def write_release_local(self):
        readWriteLock.ReadWriteLock.write_release(self)
