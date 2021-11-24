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

import argparse
import math
import random
from typing import List, Union

import matplotlib.pyplot as plt
import networkx as nx


class Edge:
    """Class for an edge in the graph."""

    def __init__(self, left_node: "Node", right_node: "Node") -> None:
        self.left_node = left_node
        self.right_node = right_node

    def __eq__(self, edge: "Edge") -> bool:
        assert isinstance(edge, Edge)
        return self.left_node == edge.left_node and self.right_node == edge.right_node

    def __repr__(self) -> str:
        return f"{self.left_node}->{self.right_node}"

    def remove(self) -> None:
        """Remove the edge from both edge lists of the nodes."""
        self.left_node.remove_edge(self.right_node)
        self.right_node.remove_edge(self.left_node)
        self.left_node = None
        self.right_node = None


class Node:
    """Class for a node in the graph."""

    def __init__(self, index: int, group: str) -> None:
        self.edges = []
        self.index = index
        self.group = group

    def __eq__(self, node: "Node") -> bool:
        assert isinstance(node, Node)
        return self.index == node.index and self.group == node.group

    def __repr__(self) -> str:
        return f"{self.group}{self.index}"

    def add_edge(self, node: "Node") -> None:
        """Add an edge connected to another node.
        The edge lists on the both nodes will be updated.
        """
        self.edges.append(Edge(self, node))
        node.edges.append(Edge(node, self))

    def remove_edge(self, node: "Node") -> None:
        """Remove an edge from the node.
        The edge lists on the both nodes will be updated.
        """
        self.edges.remove(Edge(self, node))
        node.edges.remove(Edge(node, self))

    def is_neighbor(self, node: "Node") -> bool:
        """Decide if another node is a neighbor."""
        return Edge(self, node) in self.edges

    def get_neighbors(self) -> List[Union["Switch", "Server"]]:
        return [edge.right_node for edge in self.edges]


class Switch(Node):
    def __init__(self, index: int, num_ports: int) -> None:
        super().__init__(index, "sw")
        self.num_free_ports = num_ports

    def link(self, node: "Node") -> None:
        assert self.num_free_ports > 0
        super().add_edge(node)
        self.num_free_ports -= 1
        if isinstance(node, Switch):
            node.num_free_ports -= 1

    def unlink(self, node: "Node") -> None:
        super().remove_edge(node)
        self.num_free_ports += 1
        if isinstance(node, Switch):
            node.num_free_ports += 1

    def get_linked_switches(self) -> List["Switch"]:
        return [
            neighbor
            for neighbor in super().get_neighbors()
            if isinstance(neighbor, Switch)
        ]


class Server(Node):
    def __init__(self, index) -> None:
        super().__init__(index, "sv")


class Jellyfish:
    """Jellyfish topology generator."""

    def __init__(self, num_servers: int, num_switches: int, num_ports: int) -> None:
        self.num_servers = num_servers
        self.num_switches = num_switches
        self.num_ports = num_ports

        self.num_ports_for_server = int(
            math.ceil(float(self.num_servers) / self.num_switches)
        )
        self.num_ports_for_switch = self.num_ports - self.num_ports_for_server

        self.switches_with_free_ports = []
        self.switches_without_free_ports = []
        self.servers = []

        for i in range(self.num_switches):
            switch = Switch(i, self.num_ports)
            self.switches_with_free_ports.append(switch)
            for j in range(
                i * self.num_ports_for_server, (i + 1) * self.num_ports_for_server
            ):
                server = Server(j)
                self.servers.append(server)
                switch.link(server)

    def get_num_switches_with_free_ports(self) -> int:
        return len(self.switches_with_free_ports)

    def get_num_switches_without_free_ports(self) -> int:
        return len(self.switches_without_free_ports)

    def _update_state(self, switch: Switch) -> None:
        if switch in self.switches_with_free_ports and switch.num_free_ports == 0:
            self.switches_with_free_ports.remove(switch)
            self.switches_without_free_ports.append(switch)

        if switch in self.switches_without_free_ports and switch.num_free_ports == 1:
            self.switches_without_free_ports.remove(switch)
            self.switches_with_free_ports.append(switch)

    def _connect_switches(self) -> None:
        for switch1 in random.sample(
            self.switches_with_free_ports, self.get_num_switches_with_free_ports()
        ):
            if switch1.num_free_ports == 0:
                continue

            for switch2 in random.sample(
                self.switches_with_free_ports, self.get_num_switches_with_free_ports()
            ):
                if switch1.num_free_ports == 0:
                    break

                if switch2 == switch1 or switch2.num_free_ports == 0:
                    continue

                if not switch1.is_neighbor(switch2):
                    switch1.link(switch2)
                    self._update_state(switch1)
                    self._update_state(switch2)

    def generate(self) -> None:
        while True:
            self._connect_switches()

            if self.get_num_switches_with_free_ports() == 0:
                return

            if self.get_num_switches_with_free_ports() == 1:
                if self.switches_with_free_ports[0].num_free_ports == 1:
                    return

            switch1 = random.choice(self.switches_with_free_ports)
            if switch1.num_free_ports == 1:
                switch_to_unlink = random.choice(switch1.get_linked_switches())
                switch1.unlink(switch_to_unlink)
                self._update_state(switch_to_unlink)

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

            switch2.unlink(switch3)
            switch1.link(switch2)
            switch1.link(switch3)

            self._update_state(switch1)
            self._update_state(switch2)
            self._update_state(switch3)

    def plot(self, fname: str) -> None:
        g = nx.Graph()
        graph = []
        for node in (
            self.switches_without_free_ports
            + self.switches_with_free_ports
            + self.servers
        ):
            # g.add_node(repr(node))
            for edge in node.edges:
                # g.add_edge(repr(edge.left_node), repr(edge.right_node))
                graph.append([repr(edge.left_node), repr(edge.right_node)])
        
        g.add_edges_from(graph)
        nx.draw_networkx(g, with_labels=True, node_size=100)
        plt.show()
        plt.savefig(fname)


def parse_args():
    parser = argparse.ArgumentParser(
        usage="Usage: python jellyfish.py --output --num_switches --num_ports --num_servers"
    )
    parser.add_argument(
        "--output",
        help="Output image path",
        action="store",
        type=str,
        default="Figures/jellyfish.png",
    )
    parser.add_argument(
        "--num_switches",
        help="Number of switches",
        action="store",
        type=int,
        default=20,
    )
    parser.add_argument(
        "--num_ports",
        help="Number of ports on switches",
        action="store",
        type=int,
        default=4,
    )
    parser.add_argument(
        "--num_servers", help="Number of servers", action="store", type=int, default=16
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    jellyfish = Jellyfish(
        num_switches=args.num_switches,
        num_ports=args.num_ports,
        num_servers=args.num_servers,
    )
    jellyfish.generate()
    jellyfish.plot(args.output)

