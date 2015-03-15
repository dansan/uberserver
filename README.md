# EXPERIMENTAL branch, using zmq to create a distributed, multi-master uberserver cluster
- lobby clients have a initial list of known servers, connect to random one, retrieve list of additional servers from
 one of those, choose one {random one, lower load, lower client count} to connect to
- a server can join the cluster if it is already known by one of the active (already authenticated) nodes (with a
 shared secret or something)
- a new server retrieves the list of known cluster nodes and the current
 system state from an existing node, it simultaneously joins the subscribers of state changing commands, but queues
 those until state transfer has finished, then it is added to the list of known servers for clients to connect to
- all nodes are publishers and subscribers of state changing commands, cluster wide system state will be asynchronous
 (network & processing latency) but otherwise homogeneous because of deterministic message order and processing 
- MySQL either runs as a cluster or (preferred if DB not to big) sqldump is also transferred with initial system sync

# Requirements
- sqlalchemy
- ip2c
- pyzmq

# Installation
```Shell
# git clone git@github.com:spring/uberserver.git
# virtualenv ~/virtenvs/uberserver
# source ~/virtenvs/uberserver/bin/activate
(uberserver)# pip install -r requirements.txt
```

Without further configuration this will create a SQLite database (server.db).
Performance will be OK for testing and small setups. For production use,
setup MySQL/PostgreSQL/etc.

# Usage
```
# source ~/virtenvs/uberserver/bin/activate
# ./server.py
```

# Logs
- `$PWD/server.log`
