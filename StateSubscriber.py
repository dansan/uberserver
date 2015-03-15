import logging

import zmq

logger = logging.getLogger("cluster")


class StateSubscriber(object):
    def __init__(self, context, port):
        self.context = context
        self.port = port
