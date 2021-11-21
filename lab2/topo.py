# Copyright 2021 Lin Wang

# This code is part of the Advanced Computer Networks course at Vrije 
# Universiteit Amsterdam.

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import sys
import random
import queue
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.util import dumpNodeConnections

scriptpath = "../lab2/"
sys.path.append(os.path.abspath(scriptpath))
import TopoVisualize


# Class for an edge in the graph
class Edge:
    def __init__(self):
        self.lnode = None
        self.rnode = None
    
    def remove(self):
        self.lnode.edges.remove(self)
        self.rnode.edges.remove(self)
        self.lnode = None
        self.rnode = None

# Class for a node in the graph
class Node:
    def __init__(self, id, type):
        self.edges = []
        self.id = id
        self.type = type

    # Add an edge connected to another node
    def add_edge(self, node):
        edge = Edge()
        edge.lnode = self
        edge.rnode = node
        self.edges.append(edge)
        node.edges.append(edge)
        return edge

    # Remove an edge from the node
    def remove_edge(self, edge):
        self.edges.remove(edge)

    # Decide if another node is a neighbor
    def is_neighbor(self, node):
        for edge in self.edges:
            if edge.lnode == node or edge.rnode == node:
                return True
        return False


class Jellyfish:

    def __init__(self, num_servers, num_switchList, num_ports):
        self.servers = []
        self.switchList = []
        self.generate(num_servers, num_switchList, num_ports)

    def generate(self, num_servers, num_switchList, num_ports):
        
        # TODO: code for generating the jellyfish topology
        return


class Fattree(Topo):

    def __init__(self, num_ports):
        Topo.__init__(self)
        self.servers = []
        self.switchList = []
        self.G = TopoVisualize.TopoVisualize()
        self.generate(num_ports)
        self.G.draw()

    def generate(self, num_ports):

        # TODO: code for generating the fat-tree topology
        pod = num_ports
        core_sw = (pod//2)**2
        agg_sw = pod*pod//2
        edge_sw = agg_sw
        host = pod**3//4

        # generate switchList
        # core switch


        _cnt = 0
        for j in range(pod//2):
            for i in range(pod//2):
                # sw = self.addSwitch('c10_{}_{}_{}'.format(pod, j+1, i+1))
                sw = self.addSwitch('c{}'.format(_cnt))
                _cnt += 1
                self.switchList.append(sw)

        # aggregation switch
        _cnt = 0
        for p in range(pod):
            for i in range(pod//2):
                # sw = self.addSwitch('a10_{}_{}_1'.format(p, i+(pod//2)))
                sw = self.addSwitch('a{}'.format(_cnt))
                _cnt += 1
                self.switchList.append(sw)

        # edge switch
        _cnt = 0
        for p in range(pod):
            for i in range(pod//2):
                # sw = self.addSwitch('e10_{}_{}_1'.format(p, i))
                sw = self.addSwitch('e{}'.format(_cnt))
                _cnt += 1
                self.switchList.append(sw)

        # generate links bwtween core sw and aggregation sw
        cnt = 0
        start = 0
        for core in range(core_sw):
            if cnt==pod//2:
                start = start + 1
                cnt = 0
            for port in range(pod):
                co = self.switchList[core]
                agg = self.switchList[core_sw + port*pod//2 + start]
                self.addLink(co, agg)
                self.G.addEdge([co, agg])
            cnt = cnt+1

        # generate links between aggregation sw and edge sw
        for _pod in range(pod):
            for agg in range(pod//2):
                for port in range(pod//2):
                    a = self.switchList[core_sw + _pod*pod//2 + agg]
                    edge = self.switchList[core_sw + agg_sw + _pod*pod//2 + port]
                    self.addLink(a, edge)
                    self.G.addEdge([a, edge])


        # generate links between host and edge sw
        for _pod in range(pod):
            for edge in range(pod//2):
                for port in range(pod//2):
                    e = self.switchList[core_sw + agg_sw + _pod*pod//2 + edge]
                    host = self.addHost('h10_{}_{}_{}'.format(_pod, edge, port+2))
                    self.addLink(e, host)
                    self.G.addEdge([e, host])

topos = {"fatTreeTopo":(lambda:Fattree(4))}
