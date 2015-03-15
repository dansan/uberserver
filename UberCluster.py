import os.path
from socket import gethostname
import logging
from logging.handlers import TimedRotatingFileHandler
import random

from SQLcluster import NodeHandler
import zmq

from StateSubscriber import StateSubscriber
from StatePublisher import StatePublisher

# cluster config
STATIC_HOST_LIST = {"moja.local": "BzTCRzwMF6Xx"}
CLUSTER_COM_PORT = 8310
CLIENT_COM_PORT = 8311
MY_HOSTNAME = "moja.local" or gethostname()
MY_NODE_PASSWORD = "BzTCRzwMF6Xx"

# logging
logger = logging.getLogger("cluster")
logger.setLevel(logging.DEBUG)

# log file (DEBUG)
cluster_logfile = os.path.join(os.path.dirname(__file__), "cluster.log")
fh = TimedRotatingFileHandler(cluster_logfile, when="midnight", backupCount=6)
formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-5s %(module)s.%(funcName)s:%(lineno)d  %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

# console (INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter(fmt='%(asctime)s Cluster %(levelname)-5s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
ch.setFormatter(formatter)
ch.setLevel(logging.INFO)
logger.addHandler(ch)


class UberCluster(object):
    def __init__(self, engine):
        logger.info(" ** Starting UberCluster **")
        self.nodehandler = NodeHandler(engine)
        for h, p in STATIC_HOST_LIST.items():
            self.nodehandler.add_node(h, True, False, p, 0)
        self.hostname = MY_HOSTNAME
        self.context = zmq.Context()
        self.state_subscriber = StateSubscriber(self.context, CLUSTER_COM_PORT)
        self.state_publisher = StatePublisher(self.context, CLUSTER_COM_PORT)

    def retrieve_active_nodes(self):
        nodes = list(self.nodehandler.get_nodes())
        logger.debug("nodes: %s", nodes)
        # randomize nodes list
        random.shuffle(nodes)
        for node in nodes:
            logger.debug("* node: %s", node)
            if node.hostname == self.hostname:
                continue
            try:
                zsocket = self.context.socket(zmq.REQ)
                zsocket.setsockopt(zmq.RCVTIMEO, 2000)
                try:
                    zsocket.connect("tcp://%s:%d" % (node.hostname, CLUSTER_COM_PORT))
                except:
                    self.nodehandler.modify_node(node, active=False)
                    logger.info("'%s': ZMQ.connect() failed (DNS error?).", node.hostname)
                    continue
                logger.debug("'%s': Sending 'TESTLOGIN %s %s'...", node.hostname, self.hostname, MY_NODE_PASSWORD)
                zsocket.send("TESTLOGIN %s %s" % (self.hostname, MY_NODE_PASSWORD))
                try:
                    reply = zsocket.recv()
                    logger.debug("'%s': Received reply: '%s'.", node.hostname, reply)
                except:
                    self.nodehandler.modify_node(node, active=False)
                    logger.info("'%s': Server up but cluster port closed.", node.hostname)
                    continue
                finally:
                    zsocket.close()
                if reply == "TESTLOGIN OK":
                    pass
                else:
                    self.nodehandler.modify_node(node, active=False)
                    logger.error("'%s': Authentication error (reply: '%s').", node.hostname, reply)
                    continue
            except:
                logger.exception("Connecting to host '%s'.", node)
                self.nodehandler.remove_node(node)
                continue
            logger.info("Logged into node '%s'.", node)
            break
        else:
            # no node is up, we will be the first
            logger.info("No active node found, starting as first node of cluster with hostname='%s'.", self.hostname)
            # this will not really "add", but modify the existing node entry
            self.nodehandler.add_node(self.hostname, True, False, MY_NODE_PASSWORD, 0)
            self.state_publisher.start()
