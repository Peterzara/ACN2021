# Copyright 2020 Lin Wang

# This code is part of the Advanced Computer Networks (ACN) course at VU
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

from mininet.clean import cleanup
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import lg, info
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.topo import Topo

from ft_routing import FatTree


class FatTreeNet(Topo):
    def __init__(self, ft_topo: FatTree) -> None:
        Topo.__init__(self)

        for sv in ft_topo.sv:
            self.addHost(str(sv), ip=sv.ip)

        for sw in ft_topo.sw:
            self.addSwitch(str(sw))

        for link in ft_topo.links:
            self.addLink(str(link.left_node), str(link.right_node), cls=TCLink, bw=15, delay='5ms')


if __name__ == "__main__":
    lg.setLogLevel('info')
    cleanup()

    net = Mininet(topo=FatTreeNet(FatTree(4)), controller=None, autoSetMacs=True)
    net.addController('c0', controller=RemoteController, ip="127.0.0.1", port=6653)

    info('*** Starting network ***\n')
    net.start()

    info('*** Running CLI ***\n')
    # script = 'performence.sh'
    # CLI(net, script=script)
    CLI(net)

    info('*** Stopping network ***\n')
    net.stop()
