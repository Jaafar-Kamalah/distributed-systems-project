# -----------------------------------------------------------------------------
# Distributed Systems (TDDD25)
# -----------------------------------------------------------------------------
# Author: Sergiu Rafiliu (sergiu.rafiliu@liu.se)
# Modified: 16 March 2017
#
# Copyright 2012-2017 Linkoping University
# -----------------------------------------------------------------------------

import threading
import socket
import json

"""Object Request Broker

This module implements the infrastructure needed to transparently create
objects that communicate via networks. This infrastructure consists of:

--  Strub ::
        Represents the image of a remote object on the local machine.
        Used to connect to remote objects. Also called Proxy.
--  Skeleton ::
        Used to listen to incoming connections and forward them to the
        main object.
--  Peer ::
        Class that implements basic bidirectional (Stub/Skeleton)
        communication. Any object wishing to transparently interact with
        remote objects should extend this class.

"""


class CommunicationError(Exception):
    pass


class Stub(object):

    """ Stub for generic objects distributed over the network.

    This is  wrapper object for a socket.

    """

    def __init__(self, address):
        self.address = tuple(address)

    def _rmi(self, method, *args):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(self.address) 
                reqeust = json.dumps({"method": method, "args": args}) # Marshalling
                worker = s.makefile(mode="rw")
                worker.write(reqeust + "\n")
                worker.flush()
                response = worker.readline()
                response = json.loads(response) # Unmarshalling
            except Exception as e:
                raise CommunicationError(e)
        
        if "error" in response: 
            error_class = type(response["error"]["name"], (BaseException,), {})
            raise error_class(*response["error"]["args"])
        return response["result"]

    def __getattr__(self, attr):
        """Forward call to name over the network at the given address."""
        def rmi_call(*args):
            return self._rmi(attr, *args)
        return rmi_call


class Request(threading.Thread):

    """Run the incoming requests on the owner object of the skeleton."""

    def __init__(self, owner, conn, addr):
        threading.Thread.__init__(self)
        self.addr = addr
        self.conn = conn
        self.owner = owner
        self.daemon = True
    
    def process_request(self, request):
        try:
            request_dict = json.loads(request)
            method_str = request_dict["method"]
            args = request_dict["args"]
            method = getattr(self.owner, method_str)
            result = method(*args)
            return json.dumps({"result": result})
        
        except Exception as e:
            return json.dumps({"error": {"name": type(e).__name__, "args": e.args}})

    def run(self):
        try:
            worker = self.conn.makefile(mode="rw")
            request = worker.readline()
            #print(request)
            result = self.process_request(request)
            worker.write(result + '\n')
            worker.flush()
        except Exception as e:
            print("The connection to the caller has died:")
            print("\t{}: {}".format(type(e), e))
        finally:
            self.conn.close()


class Skeleton(threading.Thread):

    """ Skeleton class for a generic owner.

    This is used to listen to an address of the network, manage incoming
    connections and forward calls to the generic owner class.

    """

    def __init__(self, owner, address):
        threading.Thread.__init__(self)
        self.address = address
        self.owner = owner
        self.daemon = True
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(self.address)
        self.server.listen(1)
        pass

    def run(self):
        while True:
            try:
                conn, addr = self.server.accept()
                req = Request(self.owner, conn, addr)
                req.start()
            except socket.error:
                continue

class Peer:

    """Class, extended by objects that communicate over the network."""

    def __init__(self, l_address, ns_address, ptype):
        self.type = ptype
        self.hash = ""
        self.id = -1
        self.address = l_address
        self.skeleton = Skeleton(self, ('', l_address[1]))
        self.name_service_address = ns_address
        self.name_service = Stub(self.name_service_address)

    # Public methods

    def start(self):
        """Start the communication interface."""

        self.skeleton.start()
        self.id, self.hash = self.name_service.register(self.type,
                                                        self.address)

    def destroy(self):
        """Unregister the object before removal."""

        self.name_service.unregister(self.id, self.type, self.hash)

    def check(self):
        """Checking to see if the object is still alive."""

        return (self.id, self.type)
