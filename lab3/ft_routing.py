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

from collections import defaultdict
from ipaddress import IPv4Address, IPv4Network

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import arp, ether_types, ethernet, ipv4, packet
from ryu.topology import event
from ryu.topology.api import get_switch, get_link

from ft_topo import FatTree


class FTRouter(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(FTRouter, self).__init__(*args, **kwargs)
        self.topo = FatTree(4)
        self.node_id_by_ip = {node.ip: str(node) for node in self.topo.nodes}

        self.switches = []
        self.links = []
        self.px_routing_table = defaultdict(list)
        self.sx_routing_table = defaultdict(list)
        self.fwd_table = defaultdict(defaultdict)

        self._gen_core_sw_routing_table()
        self._gen_agg_sw_routing_table()
        self._gen_edge_sw_routing_table()

    def _gen_core_sw_routing_table(self):
        for j in range(
            self.topo.core_sw_start_id,
            self.topo.core_sw_start_id + self.topo.num_core_sw_per_agg_sw,
        ):
            for i in range(
                self.topo.core_sw_start_id,
                self.topo.core_sw_start_id + self.topo.num_core_sw_per_agg_sw,
            ):
                sw_ip = f"10.{self.topo.num_pods}.{j}.{i}"
                sw_id = self.node_id_by_ip[sw_ip]
                for pod in range(self.topo.num_ports):
                    sw_px = f"10.{pod}.0.0/16"
                    port = pod
                    next_hop_ip = f"10.{port}.{j - self.topo.core_sw_start_id + self.topo.num_edge_sw_per_pod}.1"
                    next_hop_id = self.node_id_by_ip[next_hop_ip]
                    self.px_routing_table[sw_id].append(
                        (sw_px, next_hop_id, next_hop_ip)
                    )

    def _gen_agg_sw_routing_table(self):
        for pod in range(self.topo.num_pods):
            for switch in range(
                self.topo.num_edge_sw_per_pod,
                self.topo.num_edge_sw_per_pod + self.topo.num_agg_sw_per_pod,
            ):
                sw_ip = f"10.{pod}.{switch}.1"
                sw_id = self.node_id_by_ip[sw_ip]

                # intra-pod traffic
                for subnet in range(self.topo.num_ports // 2):
                    sw_px = f"10.{pod}.{subnet}.0/24"
                    next_hop_ip = f"10.{pod}.{subnet}.1"
                    next_hop_id = self.node_id_by_ip[next_hop_ip]
                    self.px_routing_table[sw_id].append(
                        (sw_px, next_hop_id, next_hop_ip)
                    )

                # inter-pod traffic
                for sv_id in range(
                    self.topo.sv_start_id,
                    self.topo.sv_start_id + self.topo.num_sv_per_edge_sw,
                ):
                    sw_sx = f"0.0.0.{sv_id}"
                    port = (
                        (sv_id - self.topo.sv_start_id + switch)
                        % self.topo.num_core_sw_per_agg_sw
                        + self.topo.num_edge_sw_per_agg_sw
                    )
                    next_hop_ip = f"10.{self.topo.num_pods}.{switch - self.topo.num_edge_sw_per_pod + self.topo.core_sw_start_id}.{port - 1}"
                    next_hop_id = self.node_id_by_ip[next_hop_ip]
                    self.sx_routing_table[sw_id].append(
                        (sw_sx, next_hop_id, next_hop_ip)
                    )

    def _gen_edge_sw_routing_table(self):
        # only inter-pod traffic
        for pod in range(self.topo.num_pods):
            for switch in range(self.topo.num_edge_sw_per_pod):
                sw_ip = f"10.{pod}.{switch}.1"
                sw_id = self.node_id_by_ip[sw_ip]
                for sv_id in range(
                    self.topo.sv_start_id,
                    self.topo.sv_start_id + self.topo.num_sv_per_edge_sw,
                ):
                    sw_px = f"10.{pod}.{switch}.{sv_id}/32"
                    next_hop_ip = f"10.{pod}.{switch}.{sv_id}"
                    next_hop_id = self.node_id_by_ip[next_hop_ip]
                    self.px_routing_table[sw_id].append(
                        (sw_px, next_hop_id, next_hop_ip)
                    )

                sw_px = f"0.0.0.0/0"
                next_hop_ip = f"10.{pod}.{switch + self.topo.num_edge_sw_per_pod}.1"
                next_hop_id = self.node_id_by_ip[next_hop_ip]
                self.px_routing_table[sw_id].append((sw_px, next_hop_id, next_hop_ip))

    def get_next_hop(self, sw_id, dst_sw_ip):
        priority = 2
        for prefix, next_hop_id, next_hop_ip in self.px_routing_table[sw_id]:
            if IPv4Address(dst_sw_ip) in IPv4Network(prefix):
                return next_hop_id, next_hop_ip, priority

        priority = 1
        for suffix, next_hop_id, next_hop_ip in self.sx_routing_table[sw_id]:
            if dst_sw_ip.split(".")[-1] == suffix.split(".")[-1]:
                return next_hop_id, next_hop_ip, priority

    # Topology discovery
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        # Switches and links in the network
        self.switches = [switch.dp.id for switch in get_switch(self, None)]
        self.links = get_link(self, None)
        # print(f"{len(self.switches)} Switches={self.switches}")
        # print(f"{len(self.links)} links")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install entry-miss flow entry
        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, match, actions)

    # Add a flow entry to the flow-table
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Construct flow_mod message and send it
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match, instructions=inst
        )
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        datapath = ev.msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = ev.msg.match["in_port"]

        msg_pkt = packet.Packet(ev.msg.data)
        msg_pkt_eth = msg_pkt.get_protocol(ethernet.ethernet)
        dst_mac, src_mac = msg_pkt_eth.dst, msg_pkt_eth

        if msg_pkt_eth.ethertype == ether_types.ETH_TYPE_ARP:
            self.fwd_table[dpid][src_mac] = in_port
            dst_ip = msg_pkt.get_protocol(arp.arp).dst_ip
        elif msg_pkt_eth.ethertype == ether_types.ETH_TYPE_IP:
            dst_ip = msg_pkt.get_protocol(ipv4.ipv4).dst
        else:
            return

        next_dpid, next_ip, priority = self.get_next_hop(f"sw{dpid}", dst_ip)

        out_port = ofproto.OFPP_FLOOD
        if next_ip == dst_ip:
            if dst_mac in self.fwd_table[dpid]:
                out_port = self.fwd_table[dpid][dst_mac]
            else:
                out_port = ofproto.OFPP_FLOOD
        else:
            for link in self.links:
                if link.src.dpid == dpid and f"sw{link.dst.dpid}" == next_dpid:
                    out_port = link.src.port_no
                    break
                elif link.dst.dpid == dpid and f"sw{link.src.dpid}" == next_dpid:
                    out_port = link.dst.port_no
                    break

        actions = [parser.OFPActionOutput(out_port)]

        if (
            out_port != ofproto.OFPP_FLOOD
            and msg_pkt_eth.ethertype == ether_types.ETH_TYPE_IP
        ):
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst_mac)
            # with open("results/two_level_routing_table.txt.txt", "a") as f:
            #     f.write(f'dpid:sw{dpid}, dst_id:{self.node_id_by_ip[dst_ip]}, next_dpid:{next_dpid}\n')
            self.add_flow(datapath, priority, match, actions)

        out = parser.OFPPacketOut(
            datapath=datapath,
            in_port=in_port,
            actions=actions,
            buffer_id=datapath.ofproto.OFP_NO_BUFFER,
            data=ev.msg.data,
        )

        datapath.send_msg(out)
