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

import copy
import math
import random

import matplotlib.pyplot as plt
import networkx as nx


class Edge:
    """Class for an edge in the graph."""

    def __init__(self, left_node: "Node", right_node: "Node") -> None:
        self.left_node = left_node
        self.right_node = right_node

    def remove(self) -> None:
        """Remove the edge from both edge lists of the nodes."""
        self.left_node.edges.remove(self)
        self.right_node.edges.remove(self)
        self.left_node = None
        self.right_node = None

    def __eq__(self, edge: "Edge") -> bool:
        if isinstance(edge, Edge):
            return (
                self.left_node == edge.left_node and self.right_node == edge.right_node
            )

    def __repr__(self) -> str:
        return f"{self.left_node} -> {self.right_node}"


class Node:
    """Class for a node in the graph."""

    def __init__(self, index: int, group: str) -> None:
        self.edges = []
        self.index = index
        self.group = group

    def add_edge(self, node: "Node") -> None:
        """Add an edge connected to another node.
        The edge lists on the both nodes will be updated.
        """
        self.edges.append(Edge(self, node))
        node.edges.append(Edge(node, self))

    def remove_edge(self, edge: "Edge"):
        """Remove an edge from the node."""
        self.edges.remove(edge)

    def is_neighbor(self, node: "Node") -> bool:
        """Decide if another node is a neighbor."""
        for edge in self.edges:
            if edge.left_node == node or edge.right_node == node:
                return True
        return False

    def __eq__(self, node: "Node") -> bool:
        assert isinstance(node, Node)
        return self.index == node.index and self.group == node.group

    def __repr__(self) -> str:
        return f"{self.group}{self.index}"


class Jellyfish:
    """Jellyfish topology generator."""

    def __init__(self, num_servers: int, num_switches: int, num_ports: int) -> None:
        self.num_servers = num_servers
        self.num_switches = num_switches
        self.num_ports = num_ports
        self.num_ports_for_server = int(math.ceil(float(num_servers) / num_switches))
        self.num_ports_for_switch = self.num_ports - self.num_ports_for_server

        self.switches_with_free_ports = []
        self.switches_without_free_ports = []
        self.servers = []

        for i in range(self.num_switches):
            switch = Node(i, "sw")
            self.switches_with_free_ports.append(switch)
            for j in range(
                i * self.num_ports_for_server, (i + 1) * self.num_ports_for_server
            ):
                server = Node(j, "sv")
                server.add_edge(switch)

    def get_num_switches(self, state: str) -> int:
        if state == "free":
            return len(self.switches_with_free_ports)
        elif state == "used":
            return len(self.switches_without_free_ports)
        else:
            return self.get_num_switches("free") + self.get_num_switches("used")

    def get_num_used_ports(self, switch: "Node") -> int:
        return len(switch.edges)

    def get_num_free_ports(self, switch: "Node") -> int:
        return self.num_ports - self.get_num_used_ports(switch)

    def _update_state(self, switch: "Node") -> None:
        num_used_ports = self.get_num_used_ports(switch)
        if (
            num_used_ports < self.num_ports
            and switch in self.switches_without_free_ports
        ):
            self.switches_without_free_ports.remove(switch)
            self.switches_with_free_ports.append(switch)

        elif (
            num_used_ports == self.num_ports and switch in self.switches_with_free_ports
        ):
            self.switches_with_free_ports.remove(switch)
            self.switches_without_free_ports.append(switch)

    def _connect_switches(self) -> None:
        # random.shuffle(self.switches_with_free_ports)
        old_switches_with_free_ports = copy.deepcopy(self.switches_with_free_ports)
        for switch1 in random.sample(old_switches_with_free_ports, len(old_switches_with_free_ports)):
            if switch1 in self.switches_without_free_ports:
                continue

            for switch2 in random.sample(old_switches_with_free_ports, len(old_switches_with_free_ports)):
                if switch1 in self.switches_without_free_ports:
                    break

                if switch2 == switch1 or switch2 in self.switches_without_free_ports:
                    continue

                if not switch1.is_neighbor(switch2):
                    switch1.add_edge(switch2)
                    # print(f"{switch1} connected to {switch2}")
                    self._update_state(switch1)
                    self._update_state(switch2)

    def _swap_links(self, switch1: Node, switch2: Node, switch3: Node) -> None:
        switch2.remove_edge(Edge(switch2, switch3))
        switch3.remove_edge(Edge(switch3, switch2))

        switch1.add_edge(switch2)
        switch1.add_edge(switch3)

        self._update_state(switch1)
        self._update_state(switch2)
        self._update_state(switch3)

    def generate(self) -> None:
        while True:
            self._connect_switches()

            if (self.get_num_switches("free") == 0) or (
                self.get_num_switches("used") == 1
                and self.get_num_free_ports(self.switches_with_free_ports[0]) == 1
            ):
                break

            switch1 = random.choice(self.switches_with_free_ports)

            while True:
                switch2 = random.choice(self.switches_without_free_ports)
                if not switch2.is_neighbor(switch1):
                    break

            while True:
                switch3 = random.choice(self.switches_without_free_ports)
                if all(
                    [
                        switch3 is not switch2,
                        switch3.is_neighbor(switch2),
                        not switch3.is_neighbor(switch1),
                    ]
                ):
                    break

            self._swap_links(switch1, switch2, switch3)

    def plot(self, fname: str) -> None:
        g = nx.Graph()
        for node in (
            self.switches_without_free_ports
            + self.switches_with_free_ports
            + self.servers
        ):
            g.add_node(repr(node))
            for edge in node.edges:
                g.add_edge(repr(edge.left_node), repr(edge.right_node))

        nx.draw(g, with_labels=True, node_size=100)
        plt.savefig(fname)


if __name__ == "__main__":
    jellyfish = Jellyfish(num_switches=20, num_ports=8, num_servers=16)
    jellyfish.generate()
    jellyfish.plot("Figures/jellyfish.png")
