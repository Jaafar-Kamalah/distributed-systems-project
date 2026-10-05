# Distributed Systems Project

This repository contains the source code and documentation for adistributed systems project implemented in Python. The project is organized as a series of six labs, progressing from a simple standalone database to a fully distributed, replicated database. Each lab introduces a new distributed systems concept and builds on the components developed in the previous labs.

The overall goal is to develop a distributed database for storing and accessing short messages (fortunes). By the end of the lab series, the system consists of multiple servers/peers that maintain replicated copies of the database, coordinate access to shared data using distributed locking, and communicate with clients through a peer-to-peer network. The labs cover concepts such as client-server architectures, middleware, peer-to-peer communication, name services, distributed mutual exclusion, and data replication.

## Content

The project is divided into six labs:

*  Standalone Database (lab0)
*  Client-Server Database (lab1)
*  Middleware: Object Request Brokers (lab2)
*  Middleware: Peer-to-Peer Communications (lab3)
*  Middleware: Distributed Locks (lab4)
*  Client-Server Database with Replicas (lab5)
