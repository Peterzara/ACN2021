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
    def __init__(self, id, type, ip):
        self.edges = []
        self.id = id
        self.type = type
        self.ip = ip

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

class Fattree():

    def __init__(self, num_ports):

        self.servers = []
        self.switchList = []
        self.num_ports = num_ports
        self.generate()
        
    def generate(self):

        pod = self.num_ports
        core_sw_count = (pod//2)**2
        agg_sw_count = pod*pod//2
        # edge_sw_count = agg_sw_count
        # server_count = pod**3//4

        # generate core switch
        _cnt = 0
        for j in range(pod//2):
            for i in range(pod//2):
                ip = '10.{}.{}.{}'.format(pod, j+1, i+1)
                id = 'co{}'.format(_cnt)
                swNode = Node(id, 'CORE_SWITCH', ip)
                self.switchList.append(swNode)
                _cnt += 1

        # generate aggregation switch
        _cnt = 0
        for p in range(pod):
            for i in range(pod//2):
                ip = '10.{}.{}.1'.format(p, i+(pod//2))
                id = 'a{}'.format(_cnt)
                swNode = Node(id, 'AGGREGATION_SWITCH', ip)
                self.switchList.append(swNode)
                _cnt += 1

        # generate edge switch
        _cnt = 0
        for p in range(pod):
            for i in range(pod//2):
                ip = '10.{}.{}.1'.format(p, i)
                id = 'e{}'.format(_cnt)
                swNode = Node(id, 'EDGE_SWITCH', ip)
                self.switchList.append(swNode)
                _cnt += 1

        # generate links bwtween core sw and aggregation sw
        _cnt = 0
        start = 0
        for core in range(core_sw_count):
            if _cnt == pod//2:
                start = start + 1
                _cnt = 0
            for port in range(pod):
                co = self.switchList[core]
                agg = self.switchList[core_sw_count + port*pod//2 + start]
                co.add_edge(agg)
                agg.add_edge(co)
            _cnt += 1

        # generate links between aggregation sw and edge sw
        for _pod in range(pod):
            for agg in range(pod//2):
                for port in range(pod//2):
                    a = self.switchList[core_sw_count + _pod*pod//2 + agg]
                    edge = self.switchList[core_sw_count + agg_sw_count + _pod*pod//2 + port]
                    a.add_edge(edge)
                    edge.add_edge(a)

        # generate links between server and edge sw
        _cnt = 0
        for _pod in range(pod):
            for edge in range(pod//2):
                for port in range(pod//2):
                    e = self.switchList[core_sw_count + agg_sw_count + _pod*pod//2 + edge]
                    id = 'h{}'.format(_cnt)
                    ip = '10.{}.{}.{}'.format(_pod, edge, port+2)
                    server = Node(id, 'SERVER', ip)
                    self.servers.append(server)
                    e.add_edge(server)
                    server.add_edge(a)
                    _cnt += 1

# topos = {"fatTreeTopo":(lambda:Fattree(4))}