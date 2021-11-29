# Copyright 2021 Lin Wang

# This code is part of the Advanced Computer Networks course at VU 
# Amsterdam.

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

# A dirty workaround to import topo.py from lab2

import os
import subprocess
import time

import mininet
import mininet.clean
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import lg, info
from mininet.link import TCLink
from mininet.node import Node, OVSKernelSwitch, RemoteController
from mininet.topo import Topo
from mininet.util import waitListening, custom
from typing import List

import topo

class FattreeNet(Topo):
	"""
	Create a fat-tree network in Mininet
	"""

	def _verify_valid_connection(self, parent_type: str, child_type: str) -> bool:
		""" make sure links among different type of switches are correctly set up """

		if parent_type == "CORE_SWITCH" and child_type == "AGGREGATION_SWITCH":
			return True
		elif parent_type == "AGGREGATION_SWITCH" and child_type == "EDGE_SWITCH":
			return True
		elif parent_type == "EDGE_SWITCH" and child_type == "SERVER":
			return True
		else:
			return False

	def _generate_links(self, switchList: List["Node"]) -> None:
		""" generate links among switches and servers """

		for switch in switchList:
			self.addSwitch(switch.id)

			# Traverese the neighbors of current switch
			for edge in switch.edges:
				neighbor = edge.right_node
				
				# Check if the neighbor is desired type of switch or server, if not, skip
				if self._verify_valid_connection(switch.type, neighbor.type):
					if neighbor.type == "SERVER":
						self.addHost(neighbor.id, ip=neighbor.ip)
					else:
						self.addSwitch(neighbor.id)
					self.addLink(switch.id, neighbor.id, bw=15, delay='5ms')


	def __init__(self, ft_topo):
		
		Topo.__init__(self)

		# TODO: please complete the network generation logic here
		
		self._generate_links(ft_topo.switchList)


def make_mininet_instance(graph_topo):

	net_topo = FattreeNet(graph_topo)
	net = Mininet(topo=net_topo, controller=None, autoSetMacs=True)
	net.addController('c0', controller=RemoteController, ip="127.0.0.1", port=6653)
	return net

def run(graph_topo):
	
	# Run the Mininet CLI with a given topology
	lg.setLogLevel('info')
	mininet.clean.cleanup()
	net = make_mininet_instance(graph_topo)

	info('*** Starting network ***\n')
	net.start()
	info('*** Running CLI ***\n')
	CLI(net)
	info('*** Stopping network ***\n')
	net.stop()



ft_topo = topo.Fattree(4)
run(ft_topo)
