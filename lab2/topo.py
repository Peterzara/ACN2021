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

scriptpath = "../lab2/"
sys.path.append(os.path.abspath(scriptpath))
import TopoVisualize
import jellyfish as JF


# Class for an edge in the graph
class Edge:
    def __init__(self):
        self.left_node = None
        self.right_node = None
    
    def remove(self):
        self.left_node.edges.remove(self)
        self.right_node.edges.remove(self)
        self.left_node = None
        self.right_node = None

# Class for a node in the graph
class Node:
    def __init__(self, id, type):
        self.edges = []
        self.id = id
        self.type = type

    # Add an edge connected to another node
    def add_edge(self, node):
        edge = Edge()
        edge.left_node = self
        edge.right_node = node
        self.edges.append(edge)
        node.edges.append(edge)
        return edge

    # Remove an edge from the node
    def remove_edge(self, edge):
        self.edges.remove(edge)

    # Decide if another node is a neighbor
    def is_neighbor(self, node):
        for edge in self.edges:
            if edge.left_node == node or edge.right_node == node:
                return True
        return False


class Jellyfish:

    def __init__(self, num_servers, num_switchList, num_ports):
        self.servers = []
        self.switchList = []
        self.num_servers = num_servers
        self.num_switchList = num_switchList
        self.num_ports = num_ports
        self.jf = None

    def generate(self):
        
        # TODO: code for generating the jellyfish topology
        self.jf = JF.Jellyfish(
            num_switches = self.num_switchList,
            num_ports = self.num_ports,
            num_servers = self.num_servers,
        )
        self.jf.generate()
        
        self.servers = self.jf.servers
        self.switchList.extend(self.jf.switches_with_free_ports)
        self.switchList.extend(self.jf.switches_without_free_ports)

    def plot(self):
        self.jf.plot('Figures/jellyfish.png')



class Fattree(Topo):

    def __init__(self, num_ports):

        Topo.__init__(self)
        self.servers = []
        self.switchList = []
        self.G = TopoVisualize.TopoVisualize()
        self.num_ports = num_ports
        
    def generate(self):

        pod = self.num_ports
        core_sw_count = (pod//2)**2
        agg_sw_count = pod*pod//2
        edge_sw_count = agg_sw_count
        server_count = pod**3//4

        # generate core switch
        _cnt = 0
        for j in range(pod//2):
            for i in range(pod//2):
                # sw = self.addSwitch('c10_{}_{}_{}'.format(pod, j+1, i+1))
                sw = self.addSwitch('c{}'.format(_cnt))
                _cnt += 1
                swNode = Node(sw, 'switch')
                self.switchList.append(swNode)

        # generate aggregation switch
        _cnt = 0
        for p in range(pod):
            for i in range(pod//2):
                # sw = self.addSwitch('a10_{}_{}_1'.format(p, i+(pod//2)))
                sw = self.addSwitch('a{}'.format(_cnt))
                _cnt += 1
                swNode = Node(sw, 'switch')
                self.switchList.append(swNode)

        # generate edge switch
        _cnt = 0
        for p in range(pod):
            for i in range(pod//2):
                # sw = self.addSwitch('e10_{}_{}_1'.format(p, i))
                sw = self.addSwitch('e{}'.format(_cnt))
                _cnt += 1
                swNode = Node(sw, 'switch')
                self.switchList.append(swNode)

        # generate links bwtween core sw and aggregation sw
        cnt = 0
        start = 0
        for core in range(core_sw_count):
            if cnt==pod//2:
                start = start + 1
                cnt = 0
            for port in range(pod):
                co = self.switchList[core]
                agg = self.switchList[core_sw_count + port*pod//2 + start]
                self.addLink(co.id, agg.id)
                self.G.addEdge([co.id, agg.id])

                co.add_edge(agg)
                agg.add_edge(co)

            cnt = cnt+1

        # generate links between aggregation sw and edge sw
        for _pod in range(pod):
            for agg in range(pod//2):
                for port in range(pod//2):
                    a = self.switchList[core_sw_count + _pod*pod//2 + agg]
                    edge = self.switchList[core_sw_count + agg_sw_count + _pod*pod//2 + port]
                    self.addLink(a.id, edge.id)
                    self.G.addEdge([a.id, edge.id])

                    a.add_edge(edge)
                    edge.add_edge(a)


        # generate links between server and edge sw
        for _pod in range(pod):
            for edge in range(pod//2):
                for port in range(pod//2):
                    e = self.switchList[core_sw_count + agg_sw_count + _pod*pod//2 + edge]
                    serverID = self.addHost('h10_{}_{}_{}'.format(_pod, edge, port+2))
                    server = Node(serverID, 'server')
                    self.addLink(e.id, server.id)
                    self.G.addEdge([e.id, server.id])

                    e.add_edge(server)
                    server.add_edge(a)
                    self.servers.append(server)

    def plot(self):
        self.G.draw()


# topos = {"fatTreeTopo":(lambda:Fattree(4))}