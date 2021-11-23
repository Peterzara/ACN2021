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

# Same setup for Jellyfish and Fattree
num_servers = 686
num_switches = 245
num_ports = 6

ft_topo = topo.Fattree(num_ports)
ft_topo.generate()
ft_topo.visualizeTopo()
plist = ft_topo.findShortestPath()
res = ft_topo.statisticPathResult(plist)

# jf_topo = topo.Jellyfish(num_servers, num_switches, num_ports)

# TODO: code for reproducing Figure 1(c) in the jellyfish paper

ft_data = [x/sum(res) for x in res[1:6]]
jf_data = [0,0,0,0,0]

barWidth = 0.25
fig = plt.subplots(figsize =(12, 8))

br1 = np.arange(len(ft_data))
br2 = [x + barWidth for x in br1]

plt.bar(br1, ft_data, color ='b', width = barWidth,
        edgecolor ='grey', label ='Fattree')
plt.bar(br2, jf_data, color ='r', width = barWidth,
        edgecolor ='grey', label ='Jellyfish')

plt.xlabel('Path length', fontsize = 15)
plt.ylabel('Fraction of Server', fontsize = 15)
plt.xticks([r + barWidth for r in range(len(ft_data))],
        ['2', '3', '4', '5', '6'])

plt.legend()
plt.show()












