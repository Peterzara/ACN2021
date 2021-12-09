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

#!/usr/bin/env python3

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu.lib.packet import ethernet
from ryu.ofproto import ether
from ryu.topology import event
from ryu.topology.api import get_switch, get_link

import topo
import TopoStore

class SPRouter(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SPRouter, self).__init__(*args, **kwargs)
        self.topo_net = topo.Fattree(4)
        self.topology_api_app = self
        self.TopoEntity = TopoStore.TopoStore()

    # Add a flow entry to the flow-table
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Construct flow_mod message and send it
        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    def _update_port_to_dpid_tables(self, link) -> None:
        src_dpid = link.src.dpid
        dst_dpid = link.dst.dpid
        src_port_no = link.src.port_no
        dst_port_no = link.dst.port_no
        
        if src_dpid not in self.port_to_dpid_tables:
            self.port_to_dpid_tables[src_dpid] = {src_port_no: dst_dpid}
        elif self.port_to_dpid_tables[src_dpid].get(src_port_no) is None:
            self.port_to_dpid_tables[src_dpid].update({src_port_no: dst_dpid})

        if dst_dpid not in self.port_to_dpid_tables:
            self.port_to_dpid_tables[dst_dpid] = {dst_port_no: src_dpid}
        elif self.port_to_dpid_tables[dst_dpid].get(dst_port_no) is None:
            self.port_to_dpid_tables[dst_dpid].update({dst_port_no: src_dpid})

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install entry-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        switch_list = get_switch(self.topology_api_app, None)
        links_list = get_link(self.topology_api_app, None)
        
        self.TopoEntity.switch_list = switch_list
        self.TopoEntity.link_list = links_list

        # for link in links_list:
        #     self._update_port_to_dpid_tables(link)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        pkt = packet.Packet(msg.data)
        in_port = msg.match['in_port']
        arp_pkt = pkt.get_protocol(arp.arp)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        
        if eth.ethertype == ether.ETH_TYPE_LLDP:
            return
        
        if eth.ethertype == ether.ETH_TYPE_ARP:
            # self.logger.info("ARP packet in %s %s", datapath.id, in_port)
            
            src_ip = arp_pkt.src_ip
            dst_ip = arp_pkt.dst_ip

            # Check if the src_ip exists in the topology
            if self.TopoEntity.ServerEntity.get_dpid_for_ip(ip = src_ip) is None:
                # If not, add it to the topology
                self.TopoEntity.ServerEntity.add_dpid_for_ip(
                        dpid=datapath.id, 
                        ip=src_ip, 
                        port=in_port,
                        host_mac=arp_pkt.src_mac,
                        )
            else:
                # If it exists, then update the port number
                self.TopoEntity.ServerEntity.update_port_for_ip(
                        dpid=datapath.id, 
                        ip=src_ip, 
                        port=in_port,
                        host_mac=arp_pkt.src_mac,
                        )
            # print("switchToHost")
            # print(self.TopoEntity.ServerEntity.dpid_2_ip_2_port_dict)

            # Check if the dst_ip exists in the topology
            dst_dpid = self.TopoEntity.ServerEntity.get_dpid_for_ip(ip = dst_ip)
            if dst_dpid != None:
                # If the dst_ip exists, then search the shortest path from the current switch
                prev_of_sw = self.TopoEntity.search_shortest_path(dpid=datapath.id)
                # calculate the path from the src dpid to the dst dpid
                if dst_dpid != datapath.id:
                    shortest_link_path = self.TopoEntity.calculate_link_path(src_dpid=datapath.id, dst_dpid=dst_dpid, prev_of_sw=prev_of_sw)
                    reversed_shortest_link_path = self.TopoEntity.reverse_link_path(shortest_link_path)
                    
                    self.TopoEntity.install_path_to_switch(reversed_shortest_link_path, src_ip, dst_ip)
                    self.TopoEntity.install_path_to_switch(shortest_link_path, dst_ip, src_ip)
                else:
                    # print("The src {} and dst {} are in the same switch".format(src_ip, dst_ip))
                    self.TopoEntity.install_path_to_switch(None, src_ip, dst_ip)

                if arp_pkt.opcode == arp.ARP_REQUEST:
                    self.send_arp_reply(
                        datapath, 
                        in_port, 
                        eth,
                        arp_pkt,
                        self.TopoEntity.ServerEntity.get_host_mac(dst_ip),
                        arp_pkt.dst_ip)
    
    def flood_packet(self, datapath, in_port, eth, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        out_port = ofproto.OFPP_FLOOD
        actions = [parser.OFPActionOutput(out_port)]
        data = pkt.data
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=ofproto.OFP_NO_BUFFER,
            in_port=in_port,
            actions=actions,
            data=data)
        datapath.send_msg(out)

    def send_arp_reply(self, datapath, port, pkt_eth, arp_pkt, dst_host_mac, dst_host_ip):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Build ARP reply
        arp_reply = packet.Packet()
        arp_reply.add_protocol(ethernet.ethernet(
            ethertype=pkt_eth.ethertype,
            dst=pkt_eth.src,
            src=dst_host_mac))
        arp_reply.add_protocol(arp.arp(
            opcode=arp.ARP_REPLY,
            src_mac=dst_host_mac,
            src_ip=dst_host_ip,
            dst_mac=arp_pkt.src_mac,
            dst_ip=arp_pkt.src_ip))
        arp_reply.serialize()

        # Send the packet out
        actions = [parser.OFPActionOutput(port=port)]
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=ofproto.OFP_NO_BUFFER,
            in_port=ofproto.OFPP_CONTROLLER,
            actions=actions,
            data=arp_reply.data)
        # print("send_arp_reply")
        datapath.send_msg(out)