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

from typing import List


class Edge:
    """Class for an edge in the graph."""

    def __init__(self, left_node: "Node", right_node: "Node") -> None:
        self.left_node = left_node
        self.right_node = right_node

    def __eq__(self, edge: "Edge") -> bool:
        return (
            self.left_node == edge.left_node and self.right_node == edge.right_node
        ) or (self.left_node == edge.right_node and self.right_node == edge.left_node)

    def __repr__(self) -> str:
        return f"{self.left_node}->{self.right_node}"

    def __hash__(self) -> int:
        return hash(f"{self.left_node}") + hash(f"{self.right_node}")

    def remove(self) -> None:
        """Remove the edge from both edge lists of the nodes."""
        self.left_node.remove_edge(self.right_node)
        self.right_node.remove_edge(self.left_node)
        self.left_node = None
        self.right_node = None


class Node:
    def __init__(self, index: int = -1, group: str = "", ip: str = "") -> None:
        self.edges = []
        self.index = index
        self.group = group
        self.ip = ip

    def __eq__(self, node: "Node") -> bool:
        return self.index == node.index and self.group == node.group

    def __repr__(self) -> str:
        return f"{self.group}{self.index} {self.ip}"

    def __str__(self) -> str:
        return f"{self.group}{self.index}"

    def __hash__(self) -> int:
        return hash(self.ip)

    @property
    def neighbors(self) -> List["Node"]:
        return [edge.right_node for edge in self.edges]

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


class FatTree:
    def __init__(self, num_ports: int) -> None:
        self.core_sw = []
        self.agg_sw = []
        self.edge_sw = []
        self.sv = []

        self.num_ports = num_ports
        self.num_pods = self.num_ports

        self.num_agg_sw_per_core_sw = self.num_pods
        self.num_core_sw_per_agg_sw = self.num_ports // 2
        self.num_edge_sw_per_agg_sw = self.num_ports - self.num_core_sw_per_agg_sw
        self.num_edge_sw_per_pod = self.num_edge_sw_per_agg_sw
        self.num_agg_sw_per_pod = self.num_edge_sw_per_pod
        self.num_agg_sw_per_edge_sw = self.num_agg_sw_per_pod
        self.num_sv_per_edge_sw = self.num_ports - self.num_agg_sw_per_edge_sw
        self.num_sv_per_pod = self.num_sv_per_edge_sw * self.num_edge_sw_per_pod

        self.num_sv = self.num_sv_per_pod * self.num_pods
        self.num_edge_sw = self.num_edge_sw_per_pod * self.num_pods
        self.num_agg_sw = self.num_agg_sw_per_pod * self.num_pods
        self.num_core_sw = (
            self.num_core_sw_per_agg_sw * self.num_agg_sw // self.num_ports
        )
        self.num_sw = self.num_core_sw + self.num_agg_sw + self.num_edge_sw

        self.sv_start_id = 2
        self.core_sw_start_id = 1

        self._num_sw = 1  # for giving indices to switches
        self._num_sv = 1  # for giving indices to servers

        self._gen_core_sw()
        self._gen_agg_sw()
        self._gen_edge_sw()
        self._gen_sv()
        self._gen_core_agg_links()
        self._gen_agg_edge_links()
        self._gen_edge_server_links()

    @property
    def nodes(self) -> List["Node"]:
        return self.core_sw + self.agg_sw + self.edge_sw + self.sv

    @property
    def sw(self) -> List["Node"]:
        return self.core_sw + self.agg_sw + self.edge_sw

    @property
    def links(self) -> List["Edge"]:
        links = set()
        for node in self.nodes:
            for neighbor in node.neighbors:
                links.add(Edge(node, neighbor))

        return list(links)

    def _gen_core_sw(self) -> None:
        for j in range(
            self.core_sw_start_id, self.core_sw_start_id + self.num_core_sw_per_agg_sw
        ):
            for i in range(
                self.core_sw_start_id,
                self.core_sw_start_id + self.num_core_sw_per_agg_sw,
            ):
                self.core_sw.append(
                    Node(self._num_sw, "sw", f"10.{self.num_pods}.{j}.{i}")
                )
                self._num_sw += 1

    def _gen_agg_sw(self) -> None:
        for pod in range(self.num_pods):
            for switch in range(
                self.num_edge_sw_per_pod,
                self.num_edge_sw_per_pod + self.num_agg_sw_per_pod,
            ):
                self.agg_sw.append(Node(self._num_sw, "sw", f"10.{pod}.{switch}.1"))
                self._num_sw += 1

    def _gen_edge_sw(self) -> None:
        for pod in range(self.num_pods):
            for switch in range(self.num_edge_sw_per_pod):
                self.edge_sw.append(Node(self._num_sw, "sw", f"10.{pod}.{switch}.1"))
                self._num_sw += 1

    def _gen_sv(self) -> None:
        for pod_id in range(self.num_pods):
            for switch_id in range(self.num_edge_sw_per_pod):
                for server_id in range(
                    self.sv_start_id, self.sv_start_id + self.num_sv_per_edge_sw
                ):
                    self.sv.append(
                        Node(self._num_sv, "sv", f"10.{pod_id}.{switch_id}.{server_id}")
                    )
                    self._num_sv += 1

    def _gen_core_agg_links(self) -> None:
        for i in range(self.num_core_sw):
            for j in range(self.num_agg_sw_per_core_sw):
                self.core_sw[i].add_edge(
                    self.agg_sw[
                        j * self.num_agg_sw_per_pod + i // self.num_core_sw_per_agg_sw
                    ]
                )

    def _gen_agg_edge_links(self) -> None:
        for i in range(self.num_agg_sw):
            for j in range(self.num_edge_sw_per_agg_sw):
                self.agg_sw[i].add_edge(
                    self.edge_sw[
                        i // self.num_agg_sw_per_pod * self.num_edge_sw_per_pod + j
                    ]
                )

    def _gen_edge_server_links(self) -> None:
        for i in range(self.num_edge_sw):
            for j in range(self.num_sv_per_edge_sw):
                self.edge_sw[i].add_edge(self.sv[i * self.num_sv_per_edge_sw + j])


if __name__ == "__main__":
    from mininet.clean import cleanup
    from mininet.cli import CLI
    from mininet.link import TCLink
    from mininet.log import lg, info
    from mininet.net import Mininet
    from mininet.node import RemoteController
    from mininet.topo import Topo

    class FatTreeNet(Topo):
        def __init__(self, ft_topo: FatTree) -> None:
            Topo.__init__(self)

            for sv in ft_topo.sv:
                self.addHost(str(sv), ip=sv.ip)

            for sw in ft_topo.sw:
                self.addSwitch(str(sw))

            for link in ft_topo.links:
                self.addLink(
                    str(link.left_node),
                    str(link.right_node),
                    cls=TCLink,
                    bw=15,
                    delay="5ms",
                )

    lg.setLogLevel("info")
    cleanup()

    net = Mininet(topo=FatTreeNet(FatTree(4)), controller=None, autoSetMacs=True) # xterms=True)
    net.addController("c0", controller=RemoteController, ip="127.0.0.1", port=6653)

    info("*** Starting network ***\n")
    net.start()

    info("*** Running CLI ***\n")
    CLI(net)

    info("*** Stopping network ***\n")
    net.stop()
