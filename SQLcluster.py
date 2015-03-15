import logging

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean,SmallInteger
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound


logger = logging.getLogger("cluster")

# sqlalchemy
Base = declarative_base()


class Node(Base):
    __tablename__ = 'nodes'

    id = Column(Integer, primary_key=True)
    hostname = Column(String(64))
    active = Column(Boolean)
    blacklisted = Column(Boolean)
    password = Column(String(64))
    clients = Column(SmallInteger)

    def __repr__(self):
        return "<Node(id=%d, hostname='%s', active='%s', blacklisted='%s', clients=%d, password='%s')>" % (self.id,
                self.hostname, str(self.active), str(self.blacklisted), self.clients,
                self.password[0] + "_" * (len(self.password)-2) + self.password[-1])


class NodeHandler(object):
    def __init__(self, engine):
        self.engine = engine
        self.sessionmaker = sessionmaker(bind=engine, autoflush=True)
        try:
            Base.metadata.create_all(engine)
        except:
            logger.exception("Creating database:")

    def get_nodes(self):
        session = self.sessionmaker()
        nodes = session.query(Node).filter(Node.blacklisted==False)
        session.close()
        return nodes

    def add_node(self, hostname, active, blacklisted, password, clients):
        session = self.sessionmaker()
        try:
            node = session.query(Node).filter(Node.hostname == hostname).one()
            NodeHandler._modify_node(node, active=active, blacklisted=blacklisted, password=password, clients=clients)
        except NoResultFound:
            node = Node(hostname=hostname, active=active, blacklisted=blacklisted, password=password, clients=clients)
            session.add(node)
        except:
            logger.exception("Adding node with hostname=%s, active=%s, blacklisted=%s, password=%s, clients=%s",
                             hostname, str(active), str(blacklisted), password, str(clients))
            raise
        finally:
            session.commit()
            session.close()

    def modify_node(self, node, hostname=None, active=None, blacklisted=None, password=None, clients=None):
        logger.debug("node: %s, hostname: %s, active: %s, blacklisted: %s, password: %s, clients: %s",
                     node, hostname, active, blacklisted, password, clients)
        session = self.sessionmaker()
        try:
            node = session.query(Node).filter(Node.hostname == node.hostname).one()
            logger.debug("node: %s", node)
            NodeHandler._modify_node(node, hostname=hostname, active=active, blacklisted=blacklisted,
                                     password=password, clients=clients)
        except NoResultFound:
            return self.add_node(hostname, active, blacklisted, password, clients)
        except:
            logger.exception("Adding node with hostname=%s, active=%s, blacklisted=%s, password=%s, clients=%s",
                             hostname, str(active), str(blacklisted), password, str(clients))
            raise
        finally:
            session.commit()
            session.close()

    @staticmethod
    def _modify_node(node, **kwargs):
        for k, v in kwargs.items():
            # only modify attribute if value is set and attribute exists
            if v and hasattr(node, k):
                setattr(node, k, v)

    def remove_node(self, hostname):
        session = self.sessionmaker()
        try:
            node = session.query(Node).filter(Node.hostname == hostname).one()
            session.delete(node)
            session.commit()
        except NoResultFound:
            pass
        except MultipleResultsFound:
            logger.exception("Deleting node '%s'", hostname)
        finally:
            session.close()
