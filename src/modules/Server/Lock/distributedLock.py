# -----------------------------------------------------------------------------
# Distributed Systems (TDDD25)
# -----------------------------------------------------------------------------
# Author: Sergiu Rafiliu (sergiu.rafiliu@liu.se)
# Modified: 31 July 2013
#
# Copyright 2012 Linkoping University
# -----------------------------------------------------------------------------

"""Module for the distributed mutual exclusion implementation.

This implementation is based on the second Ricart-Agrawala algorithm.
The implementation should satisfy the following requests:
    --  when starting, the peer with the smallest id in the peer list
        should get the token.
    -- access to the state of each peer (for example the request and
        token dictionaries, and the and peer_list) should be
        protected.
    --  the implementation should graciously handle situations when a
        peer dies unexpectedly. All exceptions coming from calling
        peers that have died, should be handled such as the rest of the
        peers in the system are still working. Whenever a peer has been
        detected as dead, the token, request, and peer_list
        dictionaries should be updated accordingly.
    --  when the peer that has the token (either TOKEN_PRESENT or
        TOKEN_HELD) quits, it should pass the token to some other peer.
    --  For simplicity, we shall not handle the case when the peer
        holding the token dies unexpectedly.

"""

import bisect

NO_TOKEN = 0
TOKEN_PRESENT = 1
TOKEN_HELD = 2


class DistributedLock(object):

    """Implementation of distributed mutual exclusion for a list of peers.

    Public methods:
        --  __init__(owner, peer_list)
        --  initialize()
        --  destroy()
        --  register_peer(pid)
        --  unregister_peer(pid)
        --  acquire()
        --  release()
        --  request_token(time, pid)
        --  obtain_token(token)
        --  display_status()

    """

    def __init__(self, owner, peer_list):
        self.peer_list = peer_list
        self.owner = owner
        self.time = 0
        self.token = {}
        self.request = {}
        self.state = NO_TOKEN

    def _prepare(self, token):
        """Prepare the token to be sent as a JSON message.

        This step is necessary because in the JSON standard, the key to
        a dictionary must be a string whild in the token the key is
        integer.
        """
        return list(token.items())

    def _unprepare(self, token):
        """The reverse operation to the one above."""
        return dict(token)

    # Public methods

    def initialize(self):
        """ Initialize the state, request, and token dicts of the lock.

        Since the state of the distributed lock is linked with the
        number of peers among which the lock is distributed, we can
        utilize the lock of peer_list to protect the state of the
        distributed lock (strongly suggested).

        NOTE: peer_list must already be populated when this
        function is called.

        """
        self.peer_list.lock.acquire()
        try:
            # Starts with token if this peer joined the system first
            start_with_token = False
            peer_ids = list(self.peer_list.peers.keys())
            if not peer_ids:
                start_with_token = True
            else:
                smallest_pid = min(peer_ids)
                if smallest_pid == self.owner.id:
                    start_with_token = True

            if start_with_token:
                self.state = TOKEN_PRESENT
                self.token[self.owner.id] = 0
            
            # Initialize request
            for pid in peer_ids:
                self.request[pid] = 0
        finally:
            self.peer_list.lock.release()

    def destroy(self):
        """ The object is being destroyed.

        If we have the token (TOKEN_PRESENT or TOKEN_HELD), we must
        give it to someone else.

        """
        if self.state == TOKEN_HELD:
                self.release()

        self.peer_list.lock.acquire()
        try:
            if self.state == TOKEN_PRESENT:
                peers = list(self.peer_list.peers.items())
                for pid, stub in peers:
                        try:
                            stub.obtain_token(self._prepare(self.token))
                            break
                        except Exception:
                            del self.request[pid]
                            del self.token[pid]
                            continue
        finally:
            self.peer_list.lock.release()

    def register_peer(self, pid):
        """Called when a new peer joins the system."""
        self.peer_list.lock.acquire()
        try:
            self.request[pid] = 0
            if self.state != NO_TOKEN:
                self.token[pid] = 0
        finally:
            self.peer_list.lock.release()
        

    def unregister_peer(self, pid):
        """Called when a peer leaves the system."""
        self.peer_list.lock.acquire()
        try:
            del self.request[pid]
            if self.state != NO_TOKEN:
                del self.token[pid]
        finally:
            self.peer_list.lock.release()

    def acquire(self):
        """Called when this object tries to acquire the lock."""
        print("Trying to acquire the lock...")
        if self.state == NO_TOKEN:
            self.peer_list.lock.acquire()
            try:
                peers = list(self.peer_list.peers.items())
            finally:
                self.peer_list.lock.release()
            
            # Release lock before sending requests to avoid deadlocks
            self.time += 1
            for pid, stub in peers:
                    try:
                        stub.request_token(self.time, self.owner.id)
                    except Exception:
                        del self.request[pid]
                        continue

            # Wait until token is given in obtain_token()
            with self.peer_list.lock:
                while(self.state == NO_TOKEN):
                    self.peer_list.lock.wait()

        self.state = TOKEN_HELD

    def release(self):
        """Called when this object releases the lock."""
        print("Releasing the lock...")
        self.peer_list.lock.acquire()
        try:
            if( self.state == NO_TOKEN):
                print("Token needs to be acquired before it is released.\n")
                return
            
            self.state = TOKEN_PRESENT

            # Give token to peer if it is waiting in round-robin order
            my_id = self.owner.id
            peer_ids = list(self.peer_list.peers.keys())
            bisect.insort(peer_ids, my_id)
            my_index = peer_ids.index(my_id)
            peer_ids_rr = peer_ids[my_index+1:] + peer_ids[:my_index]

            for pid in peer_ids_rr:
                if self.request[pid] > self.token[pid]:
                    self.state = NO_TOKEN
                    self.token[my_id] = self.time
                    try:
                        self.peer_list.peer(pid).obtain_token(self._prepare(self.token))
                        break
                    except:
                        del self.request[pid]
                        del self.token[pid]
                        continue
        finally:
            self.peer_list.lock.release()
        
    def request_token(self, time, pid):
        """Called when some other object requests the token from us."""

        self.peer_list.lock.acquire()
        try:
            self.request[pid] = max(self.request[pid], time)
            if self.state == TOKEN_PRESENT and self.request[pid] > self.token[pid]:
                self.token[self.owner.id] = self.time
                try:
                    self.peer_list.peer(pid).obtain_token(self._prepare(self.token))
                    self.state = NO_TOKEN
                except:
                    self.state = TOKEN_PRESENT
                    del self.request[pid]
                    del self.token[pid]
        finally:
            self.peer_list.lock.release()


    def obtain_token(self, token):
        """Called when some other object is giving us the token."""
        print("Receiving the token...")
        with self.peer_list.lock:
            self.token = self._unprepare(token)
            self.state = TOKEN_PRESENT
            self.peer_list.lock.notify()

    def display_status(self):
        """Print the status of this peer."""
        self.peer_list.lock.acquire()
        try:
            nt = self.state == NO_TOKEN
            tp = self.state == TOKEN_PRESENT
            th = self.state == TOKEN_HELD
            print("State   :: no token      : {0}".format(nt))
            print("           token present : {0}".format(tp))
            print("           token held    : {0}".format(th))
            print("Request :: {0}".format(self.request))
            print("Token   :: {0}".format(self.token))
            print("Time    :: {0}".format(self.time))
        finally:
            self.peer_list.lock.release()
