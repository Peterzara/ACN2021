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

import topo
import matplotlib.pyplot as plt
import numpy as np
import Utility as ut

# TODO: code for reproducing Figure 1(c) in the jellyfish paper

def generateFigure1c(ft_topo, jf_topo):
	ft_list = ut.findShortestPath(ft_topo.switchList, ft_topo.servers)
	jf_list = ut.findShortestPath(jf_topo.switchList, jf_topo.servers)
	ft_res = ut.statisticPathResult(ft_list)
	jf_res = ut.statisticPathResult(jf_list)

	ft_data = [x/sum(ft_res) for x in ft_res[1:7]]
	jf_data = [x/sum(jf_res) for x in jf_res[1:7]]

	barWidth = 0.25
	fig = plt.subplots(figsize =(12, 8))

	br1 = np.arange(len(ft_data))
	br2 = [x + barWidth for x in br1]

	plt.bar(br2, jf_data, color ='r', width = barWidth,
	        edgecolor ='black', label ='Jellyfish')
	plt.bar(br1, ft_data, color ='b', width = barWidth,
	        edgecolor ='black', label ='Fattree')

	plt.xlabel('Path length', fontsize = 15)
	plt.ylabel('Fraction of Server Pairs', fontsize = 15)
	plt.xticks([r + barWidth for r in range(len(ft_data))], ['1', '2', '3', '4', '5', '6'])

	plt.legend()
	plt.show()


if __name__ == "__main__":
	num_servers = 16
	num_switches = 20
	num_ports = 4

	# num_servers = 432
	# num_switches = 180
	# num_ports = 12

	# num_servers = 686
	# num_switches = 245
	# num_ports = 14

	ft_topo = topo.Fattree(num_ports)
	jf_topo = topo.Jellyfish(num_servers, num_switches, num_ports)
	ft_topo.generate()
	jf_topo.generate()
	ft_topo.plot()
	jf_topo.plot()

	# generateFigure1c(ft_topo, jf_topo)
	