from typing import Optional, Tuple
class ServerStore:
    def __init__(self):
        """
        This is a class that stores the relationship between the server and the switch
        dpid_2_ip_2_port_dict: {dpid: {src_ip: {port, host_mac}}}
        """
        self.dpid_2_ip_2_port_dict = {}
    
    def get_dpid_for_ip(self, ip) -> Optional[str]:
        for dpid in self.dpid_2_ip_2_port_dict:
            if ip in self.dpid_2_ip_2_port_dict[dpid]:
                return dpid
        return None
    
    def add_dpid_for_ip(self, dpid, ip, port, host_mac) -> None:
        self.dpid_2_ip_2_port_dict.setdefault(dpid, {})
        self.dpid_2_ip_2_port_dict[dpid][ip] = {"port_no": port, "host_mac": host_mac}
    
    def update_port_for_ip(self, dpid, ip, port, host_mac) -> None:
        self.dpid_2_ip_2_port_dict[dpid][ip]["port_no"] = port
        self.dpid_2_ip_2_port_dict[dpid][ip]["host_mac"] = host_mac
    
    def get_port_for_ip(self, dpid, ip) -> Optional[int]:
        if dpid in self.dpid_2_ip_2_port_dict:
            if ip in self.dpid_2_ip_2_port_dict[dpid]:
                return self.dpid_2_ip_2_port_dict[dpid][ip]["port_no"]
        return -1

    def get_host_mac(self, dst_ip) -> Optional[str]:
        dpid = self.get_dpid_for_ip(dst_ip)
        return self.dpid_2_ip_2_port_dict[dpid][dst_ip]["host_mac"]
