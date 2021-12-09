from typing import List, Dict, Tuple
import ServerStore

class TopoStore:
    def __init__(self):
        self.ServerEntity = ServerStore.ServerStore()
        self.switch_list = []
        self.link_list = []
    
    def search_shortest_path(self, dpid) -> list:
        """
        Find the shortest path from the source switch to other switches by using Dijkstra algorithm
        """
        MAX = 0x3f3f3f3f
        num_of_sw = len(self.switch_list)
        visited = {} # type: Dict[dpid, bool]
        dist_of_sw = {} # type: Dict[dpid, distance]
        prev_of_sw = {} # type: Dict[dpid, previous_node]
        
        # Initialize the distance of each node to MAX
        dist_of_sw[dpid] = 0
        prev_of_sw[dpid] = dpid
        visited[dpid] = False

        for sw in self.switch_list:
            if sw.dp.id != dpid:
                dist_of_sw[sw.dp.id] = MAX
                prev_of_sw[sw.dp.id] = None
                visited[sw.dp.id] = False

        while True:
            # Find the node with the minimum distance
            min_dist = MAX
            min_sw = None
            for sw in self.switch_list:
                if dist_of_sw[sw.dp.id] < min_dist and not visited[sw.dp.id]:
                    min_dist = dist_of_sw[sw.dp.id]
                    min_sw = sw.dp.id
            
            if min_sw is None:
                break
            
            visited[min_sw] = True
            
            for link in self.link_list:
                if link.src.dpid == min_sw:
                    if visited[link.dst.dpid] == True:
                        continue
                    if dist_of_sw[link.dst.dpid] != MAX:
                        if dist_of_sw[link.dst.dpid] > dist_of_sw[min_sw] + 1:
                            dist_of_sw[link.dst.dpid] = dist_of_sw[min_sw] + 1
                            prev_of_sw[link.dst.dpid] = min_sw
                    else:
                        dist_of_sw[link.dst.dpid] = dist_of_sw[min_sw] + 1
                        prev_of_sw[link.dst.dpid] = min_sw

        print("dist_of_sw: ", dist_of_sw)
        # print("prev_of_sw: ", prev_of_sw)
        self.print_all_shortest_path(prev_of_sw)
        return prev_of_sw
    
    def print_all_shortest_path(self, prew_of_sw):
        print('----------------------------------------------------')
        path = []
        pathList = []
        for key, val in prew_of_sw.items():
            path.append(key)
            path.append(val)
            while key != val:
                for _key, _val in prew_of_sw.items():
                    if _key == val:
                        path.append(_val)
                        val = _val
                        key = _key
                        break
            pathList.append(reversed(path))
            path = []
        
        for li in pathList:
            if li is None:
                continue
            temp = [1 if x > 20 else x+1 for x in li]
            print(*temp, sep='->sw')


    def calculate_link_path(self, src_dpid, dst_dpid, prev_of_sw) -> list:
        """
        Calculate the path from the source switch to the destination switch
        """
        link_path = []
        curr = dst_dpid
        while curr is not src_dpid:
            parent_sw = prev_of_sw[curr]
            if curr is None:
                # print("No path from %s to %s" % (src_dpid, dst_dpid))
                return []
            else:
                # find the LINK which connects the curr switch and the previous switch
                for link in self.link_list:
                    if link.src.dpid == curr and link.dst.dpid == parent_sw:
                        link_path.append(link)
                        curr = parent_sw
                        break
        return link_path

    def reverse_link_path(self, link_path) -> list:
        reversed_link_path = []
        for link in reversed(link_path):
            self._helper_tool(reversed_link_path, link)
        return reversed_link_path

    def _helper_tool(self, reversed_link_path, link):
        for tmp_link in self.link_list:
            if link.src.dpid == tmp_link.dst.dpid and link.dst.dpid == tmp_link.src.dpid:
                reversed_link_path.append(tmp_link)
                break

    def install_path_to_switch(self, shortest_link_path, src_ip, dst_ip) -> None:
        """
        Install the path to the destination switch
        """
        if shortest_link_path is None:
            dst_mac = self.ServerEntity.get_host_mac(dst_ip)
            dpid = self.ServerEntity.get_dpid_for_ip(src_ip)
            src_datapath = self.get_datapath(dpid)
            ofp_parser = src_datapath.ofproto_parser

            connected_port = self.ServerEntity.get_port_for_ip(
                dpid=src_datapath.id, ip=dst_ip)
            in_port = self.ServerEntity.get_port_for_ip(
                dpid=src_datapath.id, ip=src_ip)

            self._add_new_flow(dst_mac, ofp_parser, in_port,
                               src_datapath, connected_port)
            return

        for idx, link in enumerate(shortest_link_path):
            dst_mac = self.ServerEntity.get_host_mac(dst_ip)
            
            if idx == 0:
                # Install the first link
                src_datapath = self.get_datapath(link.src.dpid)
                ofp_parser = src_datapath.ofproto_parser
                connected_port = link.src.port_no
                in_port = self.ServerEntity.get_port_for_ip(link.src.dpid, src_ip)
                
                self._add_new_flow(dst_mac, ofp_parser, in_port,
                                   src_datapath, connected_port)

            if idx != len(shortest_link_path) - 1:
                # Install the middle links
                mid_datapath = self.get_datapath(link.dst.dpid)
                ofp_parser = mid_datapath.ofproto_parser
                connected_port = shortest_link_path[idx+1].src.port_no
                in_port = link.dst.port_no
                
                self._add_new_flow(dst_mac, ofp_parser, in_port,
                                   mid_datapath, connected_port)

            if idx == len(shortest_link_path) - 1:
                # Install the last link
                dst_datapath = self.get_datapath(link.dst.dpid)
                ofp_parser = dst_datapath.ofproto_parser
                connected_port_to_dst_host = self.ServerEntity.get_port_for_ip(link.dst.dpid, dst_ip)
                in_port = link.dst.port_no
                # print("[1]: ", self.ServerEntity.dpid_2_ip_2_port_dict)
                # print("[2]: ", connected_port_to_dst_host,"dst_dpid: ", link.dst.dpid, "dst_ip: ", dst_ip)
                
                if connected_port_to_dst_host > 0:
                    self._add_new_flow(dst_mac, ofp_parser, in_port, dst_datapath, connected_port_to_dst_host)
                    # print("Install the last link")
                # else:
                #     print("No port connected to the host")

    def _add_new_flow(self, dst_mac, ofp_parser, in_port, dst_datapath, connected_port_to_dst_host):
        match = ofp_parser.OFPMatch(in_port=in_port, eth_dst=dst_mac)
        actions = [ofp_parser.OFPActionOutput(port=connected_port_to_dst_host)]
        self._add_flow(dst_datapath, 1, match, actions)


    def get_datapath(self, dpid) -> object:
        """
        Get the datapath object for the switch
        """
        for switch in self.switch_list:
            if switch.dp.id == dpid:
                return switch.dp
        return None
    
    def _add_flow(self, datapath, priority, match, actions) -> None:
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        mod = parser.OFPFlowMod(
            datapath=datapath, 
            priority=priority, 
            match=match, 
            instructions=inst)
        
        datapath.send_msg(mod)