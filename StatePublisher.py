import logging

import zmq

logger = logging.getLogger("cluster")


class StatePublisher(object):
    def __init__(self, context, port):
        self.context = context
        self.port = port
        self.addr = "tcp://*:%d" % self.port

    def start(self):
        try:
            self.socket = self.context.socket(zmq.PUB)
            self.socket.bind(self.addr)
        except:
            logger.exception("Binding to %s.", self.addr)
