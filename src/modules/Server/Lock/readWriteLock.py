# -----------------------------------------------------------------------------
# Distributed Systems (TDDD25)
# -----------------------------------------------------------------------------
# Author: Sergiu Rafiliu (sergiu.rafiliu@liu.se)
# Modified: 31 July 2013
#
# Copyright 2012 Linkoping University
# -----------------------------------------------------------------------------

"""Class implementing a readers-writers lock."""

import threading


class ReadWriteLock(object):

    """Reader-Writer lock.

    Implements a lock between several threads where some of them only
    read the common resource and some of them also write it.

    Rules:
        --  all readers are allowed to read the resource in parallel,
        --  all writers are blocked when there is at least a reader
            reading the resource,
        --  only one writer is allowed to modify the resource and all
            other existing readers and writers are blocked.
    """

    def __init__(self):
        self.reader_count = 0
        self.reader_lock = threading.Lock()
        self.writer_lock = threading.Lock()
    
    # Public methods
    def read_acquire(self):
        pass    
        #
        # Your code here. Replace the pass line above.
        #

    def read_release(self):
        pass
        #
        # Your code here. Replace the pass line above.
        #

    def write_acquire(self):
        pass
        #
        # Your code here. Replace the pass line above.
        #

    def write_release(self):
        pass
        #
        # Your code here. Replace the pass line above.
        #
